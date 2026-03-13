import logging
import re
import os
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import xml2epub
from .base_converter import BaseConverter

class EpubConverter(BaseConverter):
    def convert(self, content, title="Generated Novel"):
        """Create an EPUB file from the content using xml2epub"""
        try:
            print(f"Creating EPUB for '{title}' using xml2epub...")
            
            # Use author configuration if available
            author = self.config.get('author', 'Unknown Author')
            
            # Use language configuration if available
            language_map = {
                'English': 'en',
                'Spanish': 'es',
                'French': 'fr',
                'German': 'de',
                'Italian': 'it',
                'Portuguese': 'pt'
            }
            config_lang = self.config.get('language', 'English')
            lang_code = language_map.get(config_lang, 'en')
            
            # Initialize EPUB
            book = xml2epub.Epub(title, creator=author, language=lang_code)
            
            # Define common style
            style = 'BODY { font-family: "Times New Roman", Times, serif; line-height: 1.5; text-align: justify; } h1 { text-align: center; } h2 { text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; } img.cover { max-width: 100%; height: auto; display: block; margin: auto; }'

            # Add cover if available
            if self.cover_path and Path(self.cover_path).exists():
                # xml2epub handles cover by looking for an image in a chapter or generating one.
                # To ensure our cover is used, we create a cover chapter.
                cover_content = f'<html><head><style>{style}</style></head><body><div style="text-align:center;"><img src="{self.cover_path}" alt="Cover" class="cover" /><h1>{title}</h1><p>By {author}</p></div></body></html>'
                # Use local=True to ensure it copies the local image
                cover_chapter = xml2epub.create_chapter_from_string(cover_content, title='Cover', local=True)
                book.add_chapter(cover_chapter)

            # Split content by chapters
            content_stripped = content.strip()
            chapters_raw = re.split(r'^(?=#\s+)', content_stripped, flags=re.MULTILINE)
            chapters_data = [c for c in chapters_raw if c.strip()]
            
            if not chapters_data and content_stripped:
                chapters_data = [content_stripped]
                
            for i, chapter_text in enumerate(chapters_data):
                lines = chapter_text.strip().split('\n')
                if lines[0].strip().startswith('# '):
                    chapter_title = lines[0].strip().strip('# ').strip()
                    chapter_body = '\n'.join(lines[1:]).strip()
                else:
                    chapter_title = "Introduction" if i == 0 else f"Chapter {i}"
                    chapter_body = chapter_text.strip()
                
                # Create HTML content for this chapter
                html_content = f'<html><head><style>{style}</style></head><body><h1>{chapter_title}</h1>'
                
                paragraphs = chapter_body.split('\n')
                for p in paragraphs:
                    if p.strip():
                        if p.strip().startswith('## ') or p.strip().startswith('### '):
                            # Replace scene/section titles with a simple visual separator
                            html_content += '<p style="text-align:center;">***</p>'
                        else:
                            # Basic escape
                            text = p.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_content += f'<p>{text}</p>'
                    else:
                        html_content += '<p>&nbsp;</p>'
                
                html_content += '</body></html>'
                
                # Create xml2epub chapter
                chapter = xml2epub.create_chapter_from_string(html_content, title=chapter_title)
                book.add_chapter(chapter)
            
            # Save EPUB
            # We need to patch get_cover_image because of a bug in xml2epub with Pillow 9.5.0+
            # and because we already have our own cover logic.
            filename_base = title.replace(' ', '_')
            with patch('xml2epub.epub.get_cover_image') as mock_get_cover:
                # Provide a dummy image for their internal cover generation to avoid the crash
                mock_get_cover.return_value = Image.new('RGB', (600, 800), color=(255, 255, 255))
                book.create_epub(str(self.output_dir), epub_name=filename_base)
            
            filename = self.output_dir / f"{filename_base}.epub"
            print(f"EPUB file saved at: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error creating EPUB: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
