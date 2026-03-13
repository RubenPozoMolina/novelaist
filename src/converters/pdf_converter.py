import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from .base_converter import BaseConverter

class PdfConverter(BaseConverter):
    def convert(self, content, title="Generated Novel"):
        """Create a PDF file from the content with Table of Contents"""
        try:
            filename = self.output_dir / f"{title.replace(' ', '_')}.pdf"
            doc = SimpleDocTemplate(str(filename), pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom styles for headers
            styles.add(ParagraphStyle(name='ChapterTitle', parent=styles['Heading1'], alignment=1, spaceAfter=20))
            styles.add(ParagraphStyle(name='SceneTitle', parent=styles['Heading2'], alignment=1, spaceAfter=10))
            styles.add(ParagraphStyle(name='TOCHeader', parent=styles['Heading1'], alignment=1, spaceAfter=12))
            
            story = []
            toc_entries = []
            
            # Add a cover image if available
            if self.cover_path and Path(self.cover_path).exists():
                img = Image(self.cover_path, width=400, height=600)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(PageBreak())
            
            # Title Page
            story.append(Spacer(1, 100))
            story.append(Paragraph(title.upper(), styles['Title']))
            story.append(Spacer(1, 48))
            story.append(Paragraph(f"Author: {self.config.get('author', 'Unknown Author')}", styles['Normal']))
            story.append(Paragraph(f"Date: {self.config.get('date', '')}", styles['Normal']))
            story.append(PageBreak())
            
            # Table of Contents placeholder
            story.append(Paragraph("Table of Contents", styles['TOCHeader']))
            story.append(Spacer(1, 12))
            
            # Split content by chapters to build TOC and story
            content_stripped = content.strip()
            chapters_raw = re.split(r'^(?=#\s+)', content_stripped, flags=re.MULTILINE)
            chapters_data = [c for c in chapters_raw if c.strip()]

            if not chapters_data and content_stripped:
                chapters_data = [content_stripped]
            
            for i, chapter_text in enumerate(chapters_data):
                if not chapter_text.strip():
                    continue
                
                lines = chapter_text.strip().split('\n')
                if lines[0].startswith('# '):
                    chapter_title = lines[0].strip('# ').strip()
                    chapter_body = '\n'.join(lines[1:]).strip()
                else:
                    chapter_title = lines[0].strip()
                    chapter_body = '\n'.join(lines[1:]).strip()
                
                # Add to TOC
                toc_entries.append(chapter_title)
                
                # Add to story
                story.append(Paragraph(chapter_title, styles['ChapterTitle']))
                story.append(Spacer(1, 12))
                
                paragraphs = chapter_body.split('\n')
                for p in paragraphs:
                    if p.strip():
                        if p.strip().startswith('## ') or p.strip().startswith('### '):
                            # Add a visual separator instead of the title
                            story.append(Spacer(1, 12))
                            story.append(Paragraph("***", styles['SceneTitle']))
                        else:
                            story.append(Paragraph(p.strip(), styles['Normal']))
                        story.append(Spacer(1, 6))
                    else:
                        story.append(Spacer(1, 12))
                
                story.append(PageBreak())

            # Building TOC story
            toc_story = []
            for t in toc_entries:
                toc_story.append(Paragraph(t, styles['Normal']))
                toc_story.append(Spacer(1, 6))
            
            # Rebuilding story to insert TOC properly
            final_story = []
            for item in story:
                final_story.append(item)
                if isinstance(item, Paragraph) and item.text == "Table of Contents" and item.style.name == 'TOCHeader':
                    final_story.extend(toc_story)
                    final_story.append(PageBreak())
            
            doc.build(final_story)
            print(f"PDF file saved at: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            return None
