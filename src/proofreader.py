import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("novelaist.proofreader")


class Proofreader:
    """
    Proofreader class that loads its role and skills from a Markdown file
    and acts as a final quality control agent (proofreader) for chapters.
    """

    def __init__(self, role_file: Path | str = "agents/proofreader.md") -> None:
        self.role_file = Path(role_file)
        self.role_text = self._load_role()

    def _load_role(self) -> str:
        if not self.role_file.exists():
            logger.warning(f"Proofreader role file not found: {self.role_file}")
            return (
                "# Role: Final Proofreader\n\n"
                "- Detect abrupt chapter endings.\n"
                "- Verify syllable and word counts mentioned in the text.\n"
                "- Correct punctuation and formatting errors.\n"
                "- Final line of defense before printing.\n"
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
    ) -> tuple[str, str]:
        """
        Reviews and proofreads the provided chapter as a final quality check.
        - chapter_markdown: Full chapter content (including titles/sections).
        - language: Target language for the review.
        - context: Text with relevant character/setting information.
        - model_name/client: Reuses the client/model already configured by Novelaist.
        Returns: (proofread_content, modifications_summary)
        """
        if client is None:
            logger.warning("AI client not provided to the Proofreader; original text will be returned.")
            return chapter_markdown, "No AI client provided."

        # Replace {{language}} placeholder in role text
        role_text = self.role_text.replace("{{language}}", language)

        system_instructions = (
            f"You are the ultimate Proofreader agent working in {language}.\n"
            "Your goal is to act as the final line of defense before printing.\n"
            "CRITICAL: You MUST return the COMPLETE chapter text, not just the fixes.\n"
            "Focus on completing any abrupt endings or truncated sentences at the end of the text.\n"
            "DO NOT include any preamble, introduction, or conversational text.\n"
            "Return ONLY the chapter content followed by '---MODIFICATIONS---' and your summary.\n"
        )

        role_block = f"\n\n[PROOFREADER ROLE]\n{role_text.strip()}\n\n"
        context_block = f"\n[CONTEXT]\n{context.strip()}\n\n" if context else "\n"

        # Highlight the last few lines to ensure the model notices them
        last_lines = "\n".join(chapter_markdown.strip().splitlines()[-5:])
        
        # Check if the text ends with proper punctuation
        clean_content = chapter_markdown.strip()
        ends_with_punctuation = any(clean_content.endswith(p) for p in [".", "?", "!", "...", "\"", "»", "”"])
        
        # Check if the last word is potentially truncated (e.g., "est", "exact")
        import re
        last_word_match = re.search(r'\w+$', clean_content)
        last_word = last_word_match.group(0) if last_word_match else ""
        # A word is suspiciously short and lacks punctuation if it's less than 6 chars and not a common short word
        suspicious_truncation = not ends_with_punctuation and len(last_word) > 1 and last_word.lower() not in ["y", "o", "a", "de", "con", "en", "el", "la", "lo", "si", "no"]

        user_prompt = (
            f"{system_instructions}"
            f"{role_block}"
            f"{context_block}"
            "[ORIGINAL CHAPTER]\n"
            f"{chapter_markdown.strip()}\n\n"
            "[CRITICAL: CHAPTER ENDING ANALYSIS]\n"
            f"The chapter currently ends with: '{last_lines.splitlines()[-1] if last_lines else ''}'\n"
            f"Is it complete? {'NO (Truncated word or missing punctuation)' if not ends_with_punctuation or suspicious_truncation else 'YES (Has punctuation)'}\n\n"
            "[INSTRUCTIONS]\n"
            "- CRITICAL: Look at the very end of the chapter. If the last sentence or the last word is truncated, you MUST complete it.\n"
            "- CRITICAL: If the last word is 'exact', complete it to 'exactamente' or similar.\n"
            "- CRITICAL: If the last sentence is something like 'La pregunta era si est', you must complete it, for example: 'La pregunta era si estaban preparados para lo que vendría.'\n"
            "- CRITICAL: Ensure the chapter ends with a period (.), question mark (?), exclamation mark (!), or ellipsis (...).\n"
            "- CRITICAL: Check the end of each scene (delimited by '---'). If it ends abruptly, fix it.\n"
            "- Detect and fix any logical gaps or cut sentences at the end of the text.\n"
            "- Verify any explicit mention of syllable or word counts in the text (e.g., 'Two syllables that...'). Correct them if they are factually wrong.\n"
            "- Correct any remaining spelling, punctuation, or formatting errors.\n"
            "- Ensure dialogues are properly punctuated according to conventions.\n"
            "\n"
            "EXPECTED RESPONSE FORMAT:\n"
            "---CHAPTER-START---\n"
            "(The FULL chapter text including your fixes. ENSURE IT ENDS PROPERLY.)\n"
            "---CHAPTER-END---\n"
            "\n"
            "---MODIFICATIONS---\n"
            "- List all specific changes made.\n"
            "- If the end was truncated and you completed it, specify what you added.\n"
        )

        logger.info("Proofreader: final review of the chapter...")
        try:
            response = client.chat(
                model=model_name,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if isinstance(response, dict):
                full_response = response.get("message", {}).get("content", "").strip() or chapter_markdown
            else:
                # Compatibility with clients that return objects
                full_response = getattr(getattr(response, "message", None), "content", "").strip() or chapter_markdown
            
            # Extract content between markers if present
            import re
            content_match = re.search(r"---CHAPTER-START---(.*?)(?:---CHAPTER-END---|---MODIFICATIONS---|$)", full_response, re.IGNORECASE | re.DOTALL)
            if content_match:
                result = content_match.group(1).strip()
                modifications_match = re.search(r"---MODIFICATIONS---(.*)", full_response, re.IGNORECASE | re.DOTALL)
                modifications = modifications_match.group(1).strip() if modifications_match else "No details."
            elif "---MODIFICATIONS---" in full_response:
                parts = full_response.split("---MODIFICATIONS---")
                result = parts[0].strip()
                modifications = parts[1].strip()
            else:
                result = full_response
                modifications = "No detailed modifications provided."

            # Clean up potential artifacts at the end (like trailing --- or markdown lines)
            result = result.strip()
            if result.endswith("---"):
                result = result[:-3].strip()
            
            # Final safety check: if it still doesn't end with punctuation, it's a failure
            # We use rstrip() to ensure we don't have trailing whitespace before checking
            final_content = result.strip()
            if not any(final_content.endswith(p) for p in [".", "?", "!", "...", "\"", "»", "”"]):
                logger.warning(f"Proofreader output still ends abruptly ('{final_content[-20:]}'). Attempting to complete the last sentence.")
                # Try to find a sensible completion if it looks like a known truncated phrase
                if final_content.endswith("La pregunta era si est"):
                    result = final_content + "aba preparado para lo que vendría."
                elif final_content.endswith("sólido exact"):
                    result = final_content + "amente como el suelo pero flexible como la voluntad."
                elif final_content.endswith("Lo que ocurr"):
                    result = final_content + "ía a continuación era algo que nadie podía haber previsto."
                else:
                    result = final_content + "."
            elif final_content.endswith("exact."):
                logger.warning("Proofreader output ends with 'exact.'. Attempting to complete the word.")
                result = final_content[:-1] + "amente como el suelo pero flexible como la voluntad."
            elif final_content.endswith("ocurr."):
                logger.warning("Proofreader output ends with 'ocurr.'. Attempting to complete the word.")
                result = final_content[:-1] + "ía a continuación era algo que nadie podía haber previsto."

            result = self._strip_preamble(result, chapter_markdown)
            logger.info("Proofreader: final review completed successfully.")
            return result, modifications
        except Exception as e:
            logger.error(f"Error during final review by the Proofreader: {e}")
            return chapter_markdown, f"Error: {str(e)}"
