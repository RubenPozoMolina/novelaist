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

    def _strip_preamble(self, result: str, fallback: str) -> str:
        """Remove any preamble lines added by the model before the actual translated content."""
        import re
        # If the result starts with a heading, it's clean
        if result.startswith("#"):
            return result
        # Find the first heading line and return from there
        match = re.search(r"^(#|\*\*)", result, re.MULTILINE)
        if match:
            return result[match.start():].strip()
        return fallback

    def translate_chapter(
        self,
        chapter_markdown: str,
        *,
        target_language: str = "Spanish",
        model_name: str = "command-r",
        client=None,
    ) -> str:
        """
        Translates the provided chapter to the target language, returning the final translated text.
        - chapter_markdown: Full chapter content including all markdown headers.
        - target_language: Target language for translation.
        - model_name/client: Reuses the client/model already configured by Novelaist.
        """
        if client is None:
            logger.warning("AI client not provided to the Translator; original text will be returned.")
            return chapter_markdown

        system_instructions = (
            f"You are an expert translator. Translate the following chapter to {target_language}.\n"
            "Return ONLY the translated chapter text, without any external comments or notes.\n"
            "Maintain the exact markdown structure (#, ##, ###) and formatting.\n"
            "Translate ALL content including headers, scene titles, dialogue, and narrative.\n"
        )

        role_block = f"\n\n[TRANSLATOR ROLE]\n{self.role_text.strip()}\n\n"

        user_prompt = (
            f"{system_instructions}"
            f"{role_block}"
            "[ORIGINAL CHAPTER]\n"
            f"{chapter_markdown.strip()}\n\n"
            "[INSTRUCTIONS]\n"
            "- Translate everything to {target_language}.\n"
            "- Preserve the markdown structure exactly.\n"
            "- Keep proper names, technical terms, and place names unless they have established translations.\n"
            "- Ensure the translation reads naturally in {target_language}.\n"
            "- Return ONLY the translated chapter text.\n"
        )

        logger.info(f"Translator: translating chapter to {target_language}...")
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
