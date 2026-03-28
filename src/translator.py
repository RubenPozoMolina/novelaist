import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("novelaist.translator")


class Translator:
    """
    Translator class that loads its role and instructions from a Markdown file
    and translates chapters to the target language.
    """

    def __init__(self, role_file: Path | str = "agents/translator.md") -> None:
        self.role_file = Path(role_file)
        self.role_text = self._load_role()

    def _load_role(self) -> str:
        if not self.role_file.exists():
            logger.warning(f"Translator role file not found: {self.role_file}")
            return (
                "# Role: Expert Translator\n\n"
                "- Translate faithfully preserving meaning, tone, and style.\n"
                "- Keep markdown structure and headers intact.\n"
                "- Return ONLY the translated text, no comments or notes.\n"
            )
        try:
            return self.role_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not read {self.role_file}: {e}")
            return ""

    # Patterns that indicate a line is a leaked instruction, not real content
    _INSTRUCTION_PATTERNS = [
        r"return only",
        r"translated chapter text",
        r"no comments or notes",
        r"preserve the markdown",
        r"maintain the exact markdown",
        r"translate (all|everything|faithfully)",
        r"^\[instructions\]",
        r"^\[original chapter\]",
        r"^\[translator role\]",
    ]

    def _is_instruction_line(self, line: str) -> bool:
        """Return True if the line looks like a leaked prompt instruction."""
        import re
        clean = line.lstrip("#").strip().lower()
        return any(re.search(pat, clean) for pat in self._INSTRUCTION_PATTERNS)

    def _strip_preamble(self, result: str, fallback: str) -> str:
        """Remove any preamble lines added by the model before the actual translated content."""
        import re
        lines = result.splitlines()
        # Drop leading lines that are leaked instructions (even if they start with #)
        while lines and self._is_instruction_line(lines[0]):
            lines.pop(0)
        result = "\n".join(lines).strip()
        if not result:
            return fallback
        # If the result now starts with a heading, it's clean
        if result.startswith("#"):
            return result
        # Find the first heading line and return from there
        match = re.search(r"^(#|\*\*)", result, re.MULTILINE)
        if match:
            return result[match.start():].strip()
        return result if result else fallback

    def translate_chapter(
        self,
        chapter_markdown: str,
        *,
        source_language: str = "English",
        target_language: str = "Spanish",
        model_name: str = "command-r",
        client=None,
    ) -> str:
        """
        Translates the provided chapter from source to target language, returning the final translated text.
        - chapter_markdown: Full chapter content including all markdown headers.
        - source_language: Source language of the original text.
        - target_language: Target language for translation.
        - model_name/client: Reuses the client/model already configured by Novelaist.
        """
        if client is None:
            logger.warning("AI client not provided to the Translator; original text will be returned.")
            return chapter_markdown
        
        # Skip translation if source and target languages are the same
        if source_language.lower() == target_language.lower():
            logger.info(f"Translator: source and target languages are the same ({source_language}), skipping translation.")
            return chapter_markdown

        # Replace {{source_language}} and {{target_language}} placeholders in role text
        role_text = self.role_text.replace("{{source_language}}", source_language).replace("{{target_language}}", target_language)

        system_instructions = (
            f"You are an expert translator. Translate the following chapter from {source_language} to {target_language}.\n"
            "Return ONLY the translated chapter text, without any external comments or notes.\n"
            "Maintain the exact markdown structure (#, ##, ###) and formatting.\n"
            "Translate ALL content including headers, scene titles, dialogue, and narrative.\n"
        )

        role_block = f"\n\n[TRANSLATOR ROLE]\n{role_text.strip()}\n\n"

        user_prompt = (
            f"{system_instructions}"
            f"{role_block}"
            "[ORIGINAL CHAPTER]\n"
            f"{chapter_markdown.strip()}\n\n"
            "[INSTRUCTIONS]\n"
            f"- Translate everything from {source_language} to {target_language}.\n"
            "- Preserve the markdown structure exactly.\n"
            "- Keep proper names, technical terms, and place names unless they have established translations.\n"
            f"- Ensure the translation reads naturally in {target_language}.\n"
            "- Return ONLY the translated chapter text.\n"
        )

        logger.info(f"Translator: translating chapter from {source_language} to {target_language}...")
        try:
            response = client.chat(
                model=model_name,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if isinstance(response, dict):
                result = response.get("message", {}).get("content", "").strip() or chapter_markdown
            else:
                # Compatibility with clients that return objects
                result = getattr(getattr(response, "message", None), "content", "").strip() or chapter_markdown
            result = self._strip_preamble(result, chapter_markdown)
            logger.info("Translator: chapter translation completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error during chapter translation: {e}")
            return chapter_markdown
