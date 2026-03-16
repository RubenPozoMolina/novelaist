import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("novelaist.editor")


class Editor:
    """
    Editor class that loads its role and skills from a Markdown file
    and acts as a reviewer agent after each chapter is created.
    """

    def __init__(self, role_file: Path | str = "agents/editor.md") -> None:
        self.role_file = Path(role_file)
        self.role_text = self._load_role()

    def _load_role(self) -> str:
        if not self.role_file.exists():
            logger.warning(f"Editor role file not found: {self.role_file}")
            return (
                "# Role: Literary Editor\n\n"
                "- Style and clarity improvement.\n"
                "- Grammar and spelling correction.\n"
                "- Maintain consistency with characters and setting.\n"
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
        outline: Optional[str] = None,
        model_name: str = "command-r",
        client=None,
    ) -> str:
        """
        Reviews and improves the provided chapter, returning the final revised text.
        - chapter_markdown: Full chapter content (including titles/sections).
        - language: Target language for the review.
        - context: Text with relevant character/setting information.
        - outline: Chapter outline to validate coherence.
        - model_name/client: Reuses the client/model already configured by Novelaist.
        """
        if client is None:
            logger.warning("AI client not provided to the Editor; original text will be returned.")
            return chapter_markdown

        system_instructions = (
            f"You are an expert literary editor working in {language}.\n"
            "Your goal is to return ONLY the revised chapter, without external comments or notes.\n"
            "Maintain the heading structure (#, ##, ###) and sections of the original text,\n"
            "improving style, rhythm, grammar, and narrative consistency.\n"
        )

        role_block = f"\n\n[EDITOR ROLE]\n{self.role_text.strip()}\n\n"
        context_block = f"\n[CONTEXT]\n{context.strip()}\n\n" if context else "\n"
        outline_block = f"\n[CHAPTER OUTLINE]\n{outline.strip()}\n\n" if outline else "\n"

        user_prompt = (
            f"{system_instructions}"
            f"{role_block}"
            f"{context_block}"
            f"{outline_block}"
            "[ORIGINAL CHAPTER]\n"
            f"{chapter_markdown.strip()}\n\n"
            "[INSTRUCTIONS]\n"
            "- Rewrite the chapter in the same language improving literary quality.\n"
            "- Preserve the structure and essential content of each section.\n"
            "- Ensure consistency with characters and setting.\n"
            "- Return ONLY the revised chapter text, without additional prologues or epilogues.\n"
        )

        logger.info("Editor: reviewing and improving the chapter...")
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
            logger.info("Editor: chapter review completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error during chapter review by the Editor: {e}")
            return chapter_markdown
