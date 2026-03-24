import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("novelaist.grammar_corrector")


class GrammarCorrector:
    """
    GrammarCorrector class that loads its role and skills from a Markdown file
    and acts as a grammar/spelling corrector agent for chapters.
    """

    def __init__(self, role_file: Path | str = "agents/grammar_corrector.md") -> None:
        self.role_file = Path(role_file)
        self.role_text = self._load_role()

    def _load_role(self) -> str:
        if not self.role_file.exists():
            logger.warning(f"GrammarCorrector role file not found: {self.role_file}")
            return (
                "# Role: Grammar Corrector\n\n"
                "- Correct spelling errors.\n"
                "- Fix grammar and punctuation.\n"
                "- Maintain the original text structure and content.\n"
            )
        try:
            return self.role_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not read {self.role_file}: {e}")
            return ""

    def _strip_preamble(self, result: str, fallback: str) -> str:
        """Remove any preamble lines added by the model before the actual chapter content."""
        import re
        # If the result starts with a heading, it's clean
        if result.startswith("#"):
            return result
        # Find the first heading line and return from there
        match = re.search(r"^(#|\*\*)", result, re.MULTILINE)
        if match:
            return result[match.start():].strip()
        return fallback

    def review_chapter(
        self,
        chapter_markdown: str,
        *,
        language: str = "Spanish",
        context: Optional[str] = None,
        model_name: str = "command-r",
        client=None,
    ) -> str:
        """
        Reviews and corrects grammar/spelling of the provided chapter, returning the final corrected text.
        - chapter_markdown: Full chapter content (including titles/sections).
        - language: Target language for the review.
        - context: Text with relevant character/setting information.
        - model_name/client: Reuses the client/model already configured by Novelaist.
        """
        if client is None:
            logger.warning("AI client not provided to the GrammarCorrector; original text will be returned.")
            return chapter_markdown

        system_instructions = (
            f"You are an expert grammar corrector working in {language}.\n"
            "Your goal is to return ONLY the corrected chapter, without external comments or notes.\n"
            "Maintain the heading structure (#, ##, ###) and sections of the original text,\n"
            "correcting only spelling, grammar, and punctuation errors.\n"
            "Do NOT change the style, content, or narrative of the text.\n"
        )

        role_block = f"\n\n[GRAMMAR CORRECTOR ROLE]\n{self.role_text.strip()}\n\n"
        context_block = f"\n[CONTEXT]\n{context.strip()}\n\n" if context else "\n"

        user_prompt = (
            f"{system_instructions}"
            f"{role_block}"
            f"{context_block}"
            "[ORIGINAL CHAPTER]\n"
            f"{chapter_markdown.strip()}\n\n"
            "[INSTRUCTIONS]\n"
            "- Correct spelling, grammar, and punctuation errors only.\n"
            "- Preserve the exact structure and content of each section.\n"
            "- Ensure proper accentuation and punctuation.\n"
            "- Return ONLY the corrected chapter text, without additional prologues or epilogues.\n"
        )

        logger.info("GrammarCorrector: reviewing chapter for spelling and grammar...")
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
            logger.info("GrammarCorrector: chapter review completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error during chapter review by the GrammarCorrector: {e}")
            return chapter_markdown
