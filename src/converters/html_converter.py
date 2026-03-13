import re
from pathlib import Path
from .base_converter import BaseConverter

class HtmlConverter(BaseConverter):
    def convert(self, content, title="Generated Novel"):
        """Create a single HTML file from the content for debugging/preview"""
        try:
            author = self.config.get('author', 'Unknown Author')
            style = 'BODY { font-family: "Times New Roman", Times, serif; line-height: 1.5; text-align: justify; max-width: 800px; margin: auto; padding: 20px; } h1 { text-align: center; } h2 { text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; } h3 { border-bottom: 1px dotted #eee; } img.cover { max-width: 100%; height: auto; display: block; margin: auto; } .cover-page { background-color: #000; color: #fff; padding: 50px; text-align: center; margin-bottom: 50px; }'
            
            html_content = f'<!DOCTYPE html><html><head><title>{title}</title><meta charset="UTF-8"><style>{style}</style></head><body>'
            
            # Add cover if available
            if self.cover_path and Path(self.cover_path).exists():
                cover_rel_path = Path(self.cover_path).name
                html_content += f'<div class="cover-page"><img src="{cover_rel_path}" alt="Cover" class="cover" /><h1>{title}</h1><p>By {author}</p></div>'

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
                
                html_content += f'<h1>{chapter_title}</h1>'
                
                paragraphs = chapter_body.split('\n')
                for p in paragraphs:
                    if p.strip():
                        if p.strip().startswith('## ') or p.strip().startswith('### '):
                            # Replace scene/section titles with a simple visual separator
                            html_content += '<h2 style="text-align:center;">***</h2>'
                        else:
                            text = p.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_content += f'<p>{text}</p>'
                    else:
                        html_content += '<p>&nbsp;</p>'
                
                html_content += '<hr>'

            html_content += '</body></html>'
            
            filename = self.output_dir / f"{title.replace(' ', '_')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML file saved at: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error creating HTML: {str(e)}")
            return None
