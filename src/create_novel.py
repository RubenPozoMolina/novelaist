import argparse
import json
import ollama
import subprocess
from pathlib import Path
try:
    from src.cover_generator import CoverGenerator
except ImportError:
    from cover_generator import CoverGenerator

from ebooklib import epub
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image


def process_character_document(file_path):
    """Process a character document"""
    with open(file_path, 'r') as f:
        content = f.read()
    return content


def process_chapter_document(file_path):
    """Process a chapter document"""
    with open(file_path, 'r') as f:
        content = f.read()
    return content


class Novelaist:
    def __init__(self, examples_directory="examples", output_directory="output"):
        self.examples_dir = Path(examples_directory)
        self.output_dir = Path(output_directory)
        
        # Ensure the output directory exists from the start
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
        
        self.documents = {
            "characters": [],
            "chapters": [],
            "environment": []
        }
        self._load_documents()
        self.cover_generator = CoverGenerator()
        self.cover_path = None
    
    def _load_config(self):
        """Load configuration from the config.json file"""
        config_path = self.examples_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json: {str(e)}")
                return {}
        return {}
    
    def _load_documents(self):
        """Load example documents from the examples directory"""
        # Load character documents
        characters_dir = self.examples_dir / "characters"
        if characters_dir.exists():
            for f in characters_dir.glob("*.md"):
                self.documents["characters"].append(f)
        
        # Load chapter documents
        chapters_dir = self.examples_dir / "chapters"
        if chapters_dir.exists():
            for f in chapters_dir.glob("*.md"):
                self.documents["chapters"].append(f)
        
        # Load environment documents
        environment_dir = self.examples_dir / "environment"
        if environment_dir.exists():
            for f in environment_dir.glob("*.md"):
                self.documents["environment"].append(f)
    
    def get_document_structure(self):
        """Get the structure of loaded documents"""
        return self.documents

    def generate_novel_content(self):
        """Generate novel content based on loaded documents, chapter by chapter."""
        print("Generating novel content...")
        
        # Process documents to create context
        character_info = []
        environment_info = []
        
        # Process characters
        for character_file in self.documents["characters"]:
            content = process_character_document(character_file)
            character_info.append(content)
        
        # Process environment
        for env_file in self.documents["environment"]:
            with open(env_file, 'r') as f:
                content = f.read()
            environment_info.append(content)
        
        context = f"""
        Characters:
        {chr(10).join(character_info)}
        
        Environment:
        {chr(10).join(environment_info)}
        
        Novel title: {self.config.get('novel_title', 'Generated Novel')}
        Author: {self.config.get('author', 'Unknown Author')}
        """
        
        language = self.config.get('language', 'English')
        min_words = int(self.config.get('minimum_chapter_words_number', '1000'))
        sections_count = int(self.config.get('chapter_sections', 3))
        words_per_section = min_words // sections_count
        
        # Sort chapters to ensure they are processed in order
        sorted_chapters = sorted(self.documents["chapters"])
        
        full_novel_content = []
        
        # Generate content using the configured model
        model_name = self.config.get('model', 'command-r')
        host = self.config.get('host')
        
        if host:
            print(f"Connecting to {model_name} on {host}...")
            client = ollama.Client(host=host)
        else:
            print(f"Connecting to {model_name}...")
            client = ollama
            
        for chapter_index, chapter_file in enumerate(sorted_chapters, 1):
            chapter_name = chapter_file.stem
            output_chapter_file = self.output_dir / f"{chapter_name}_generated.md"
            
            if output_chapter_file.exists():
                print(f"Chapter {chapter_name} ({chapter_index}/{len(sorted_chapters)}) already exists. Loading from file...")
                with open(output_chapter_file, 'r') as f:
                    chapter_content = f.read()
                full_novel_content.append(chapter_content)
                continue
                
            print(f"Generating chapter: {chapter_name} ({chapter_index}/{len(sorted_chapters)})...")
            chapter_outline = process_chapter_document(chapter_file)
            
            chapter_sections_content = []
            
            for section_num in range(1, sections_count + 1):
                print(f"  - Generating section {section_num} of {sections_count}...")
                
                previous_sections_context = ""
                if chapter_sections_content:
                    previous_sections_context = "\n\nContext from previous sections of this chapter:\n" + "\n\n".join(chapter_sections_content[-2:]) # Keep last 2 sections for context

                prompt = f"""
                {context}
                
                Language: {language}
                
                Current Chapter Outline:
                {chapter_outline}
                
                {previous_sections_context}
                
                Instructions:
                1. Write section {section_num} of {sections_count} for this chapter in {language}.
                2. This section should have approximately {words_per_section} words.
                3. Maintain consistency with the provided Characters, Environment, and previous sections.
                4. Use Markdown formatting for this section (### Section Title).
                5. Focus ONLY on the part of the outline corresponding to this section.
                
                Generate the literary content for this section now.
                """
                
                response = client.chat(
                    model=model_name,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                
                # In ollama-python 0.1.x, response is a dict with ['message']['content']
                if isinstance(response, dict):
                    section_content = response['message']['content']
                else:
                    section_content = response.message.content
                
                chapter_sections_content.append(section_content)
            
            chapter_content = "\n\n".join(chapter_sections_content)
                
            # Save individual chapter
            with open(output_chapter_file, 'w') as f:
                f.write(chapter_content)
                
            full_novel_content.append(chapter_content)
            
        return "\n\n".join(full_novel_content)


    
    def generate_cover(self):
        """Generate a cover for the novel and add text (title, author, model)."""
        title = self.config.get('novel_title', 'Generated Novel')
        author = self.config.get('author', 'Unknown Author')
        model = self.config.get('model', 'command-r')
        
        # Simple description based on environmental documents if available
        description = ""
        if self.documents["environment"]:
            with open(self.documents["environment"][0], 'r') as f:
                description = f.read()[:200].replace('\n', ' ')
        
        cover_filename = f"{title.replace(' ', '_')}_cover.png"
        output_path = self.output_dir / cover_filename
        
        # Check if cover already exists
        if output_path.exists():
            print(f"Cover already exists at: {output_path}. Skipping generation.")
            self.cover_path = str(output_path)
            return self.cover_path
            
        # Generate the background image
        generated_path = self.cover_generator.generate_cover(title, description, output_path)
        
        if generated_path:
            # Add text to the generated image
            self._add_text_to_cover(generated_path, title, author, model)
            self.cover_path = generated_path
            
        return self.cover_path

    def _add_text_to_cover(self, image_path, title, author, model):
        """Add title, author, and model text to the cover image."""
        try:
            img = PILImage.open(image_path)
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Try to load a font, fallback to default
            try:
                # Common paths for fonts in Linux
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                    "DejaVuSans-Bold.ttf"
                ]
                font_title = None
                for path in font_paths:
                    if Path(path).exists():
                        font_title = ImageFont.truetype(path, int(height * 0.08))
                        font_author = ImageFont.truetype(path, int(height * 0.04))
                        font_model = ImageFont.truetype(path, int(height * 0.02))
                        break
                
                if not font_title:
                    font_title = ImageFont.load_default()
                    font_author = ImageFont.load_default()
                    font_model = ImageFont.load_default()
            except Exception:
                font_title = ImageFont.load_default()
                font_author = ImageFont.load_default()
                font_model = ImageFont.load_default()

            # Add Title (top)
            title_text = title.upper()
            left, top, right, bottom = draw.textbbox((0, 0), title_text, font=font_title)
            w, h = right - left, bottom - top
            draw.text(((width - w) / 2, height * 0.1), title_text, font=font_title, fill="white", stroke_width=2, stroke_fill="black")
            
            # Add Author (bottom-ish)
            author_text = f"By {author}"
            left, top, right, bottom = draw.textbbox((0, 0), author_text, font=font_author)
            w, h = right - left, bottom - top
            draw.text(((width - w) / 2, height * 0.8), author_text, font=font_author, fill="white", stroke_width=1, stroke_fill="black")
            
            # Add Model (bottom)
            model_text = f"Generated with {model}"
            left, top, right, bottom = draw.textbbox((0, 0), model_text, font=font_model)
            w, h = right - left, bottom - top
            draw.text(((width - w) / 2, height * 0.9), model_text, font=font_model, fill="lightgray", stroke_width=1, stroke_fill="black")
            
            img.save(image_path)
            print(f"Text added to cover: {image_path}")
        except Exception as e:
            print(f"Error adding text to cover: {str(e)}")

    def create_epub(self, content, title="Generated Novel"):
        """Create an EPUB file from the content"""
        try:
            book = epub.EpubBook()
            book.set_identifier('id123456')
            book.set_title(title)
            
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
            book.set_language(lang_code)
            
            # Use author configuration if available
            author = self.config.get('author', 'Unknown Author')
            book.add_author(author)
            
            # Convert newlines to paragraphs for basic HTML formatting
            formatted_content = ""
            paragraphs = content.split('\n')
            for p in paragraphs:
                if p.strip():
                    formatted_content += f'<p>{p.strip()}</p>'
                else:
                    formatted_content += '<br/>'

            # Add cover if available
            if self.cover_path and Path(self.cover_path).exists():
                book.set_cover("cover.png", open(self.cover_path, 'rb').read())
                
                # Add a cover page at the beginning of the spine
                cover_page = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang=lang_code)
                cover_page.content = f'<div style="text-align: center;"><img src="cover.png" alt="Cover" style="max-width: 100%;"/></div>'
                book.add_item(cover_page)
                
                # Define style - ensure a readable serif font for novels
                style = 'BODY { font-family: "Times New Roman", Times, serif; line-height: 1.5; text-align: justify; }'
                nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
                book.add_item(nav_css)
                
                # Create chapter
                chapter = epub.EpubHtml(title='Introduction', file_name='chap_01.xhtml', lang=lang_code)
                chapter.content = f'<h1>{title}</h1>{formatted_content}'
                book.add_item(chapter)
                
                # Generate table of contents
                book.toc = [epub.Link('chap_01.xhtml', title, 'intro')]
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                # Apply style
                book.spine = ['nav', cover_page, chapter]
            else:
                # Define style - ensure a readable serif font for novels
                style = 'BODY { font-family: "Times New Roman", Times, serif; line-height: 1.5; text-align: justify; }'
                nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
                book.add_item(nav_css)
                
                # Create chapter
                chapter = epub.EpubHtml(title='Introduction', file_name='chap_01.xhtml', lang=lang_code)
                chapter.content = f'<h1>{title}</h1>{formatted_content}'
                book.add_item(chapter)
                
                # Generate table of contents
                book.toc = [epub.Link('chap_01.xhtml', title, 'intro')]
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                
                # Apply style
                book.spine = ['nav', chapter]
            
            # Save file
            filename = self.output_dir / f"{title.replace(' ', '_')}.epub"
            epub.write_epub(filename, book, {})
            print(f"EPUB file saved at: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error creating EPUB: {str(e)}")
            return None

    def create_pdf(self, content, novel_title="Generated Novel"):
        """Create a PDF file from the content"""
        try:
            filename = self.output_dir / f"{novel_title.replace(' ', '_')}.pdf"
            doc = SimpleDocTemplate(str(filename), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add a cover image if available
            if self.cover_path and Path(self.cover_path).exists():
                img = Image(self.cover_path)
                # Scale the image to fit page width while maintaining an aspect ratio
                page_width, page_height = letter
                img.drawHeight = page_height * 0.7
                img.drawWidth = page_width * 0.8
                story.append(img)
                story.append(Spacer(1, 36))
            
            # Title
            title_para = Paragraph(novel_title, styles['Title'])
            story.append(title_para)
            story.append(Spacer(1, 12))
            
            # Author
            author_para = Paragraph(f"Author: {self.config.get('author', 'Unknown Author')}", styles['Normal'])
            story.append(author_para)
            story.append(Spacer(1, 12))
            
            # Date
            date_para = Paragraph(f"Date: {self.config.get('date', '')}", styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 12))
            
            # Content - split into paragraphs for PDF
            paragraphs = content.split('\n')
            for p in paragraphs:
                if p.strip():
                    content_para = Paragraph(p.strip(), styles['Normal'])
                    story.append(content_para)
                    story.append(Spacer(1, 6))
                else:
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            print(f"PDF file saved at: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            return None

    def create_mobi(self, content, novel_title="Generated Novel"):
        """Create a MOBI file from the content using ebook-convert (Calibre)"""
        try:
            # First, create the EPUB to use as a base
            epub_path = self.create_epub(content, novel_title)
            if not epub_path:
                print("Error: Could not create EPUB base for MOBI conversion.")
                return None
                
            mobi_filename = self.output_dir / f"{novel_title.replace(' ', '_')}.mobi"
            
            print(f"Converting EPUB to MOBI for '{novel_title}'...")
            # Use ebook-convert from Calibre
            try:
                subprocess.run(['ebook-convert', epub_path, str(mobi_filename)], 
                               check=True, capture_output=True, text=True)
                print(f"MOBI file saved at: {mobi_filename}")
                return str(mobi_filename)
            except subprocess.CalledProcessError as e:
                print(f"Error in ebook-convert: {e.stderr}")
                return None
            except FileNotFoundError:
                print("Error: 'ebook-convert' not found. Please install Calibre to support MOBI output.")
                return None
        except Exception as e:
            print(f"Error creating MOBI: {str(e)}")
            return None

    def save_output(self, content, filename):
        """Save generated content in the output folder"""
        output_file = self.output_dir / filename
        try:
            # Include cover in Markdown if it exists
            if filename.endswith('.md') and self.cover_path:
                cover_rel_path = Path(self.cover_path).name
                content = f"![Cover]({cover_rel_path})\n\n# {self.config.get('novel_title', 'Generated Novel')}\n\n{content}"
                
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"Content saved at: {output_file}")
        except Exception as e:
            print(f"Error saving file: {str(e)}")

if __name__ == "__main__":
    # Process input parameters
    parser = argparse.ArgumentParser(description="Generate a novel using local AI.")
    parser.add_argument("examples_dir", help="Path to the directory containing example documents.")
    parser.add_argument("output_dir", help="Path to the directory where output files will be saved.")
    
    args = parser.parse_args()
    
    # Create a Novelaist instance with input parameters
    novelaist = Novelaist(args.examples_dir, args.output_dir)
    
    # Show document structure
    print("Document structure:")
    docs = novelaist.get_document_structure()
    for category, files in docs.items():
        print(f"  {category}: {len(files)} files")
        for file in files:
            print(f"    - {file.name}")
    
    # Test processing of a document
    if docs["characters"]:
        print("\nContent of first character document:")
        print(process_character_document(docs["characters"][0]))
    
    # Test generation
    print("\n" + "="*50)
    
    # Generate cover
    print("Generating cover...")
    novelaist.generate_cover()
    
    generated_content = novelaist.generate_novel_content()
    print("Generation completed.")
    
    # Save result in output files
    print("\n" + "="*50)
    print("Generating files in EPUB, MOBI and PDF formats...")
    
    # Create files in different formats
    title = novelaist.config.get('novel_title', 'Generated Novel')
    novelaist.create_epub(generated_content, title)
    novelaist.create_pdf(generated_content, title)
    novelaist.create_mobi(generated_content, title)
    
    # Also save the original Markdown file
    markdown_filename = f"{title.replace(' ', '_')}.md"
    novelaist.save_output(generated_content, markdown_filename)
    
    print("Process completed successfully.")