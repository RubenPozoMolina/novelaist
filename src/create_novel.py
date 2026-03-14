import argparse
import json
import logging
import ollama
import subprocess
import datetime
from pathlib import Path
try:
    from src.cover_generator import CoverGenerator
except ImportError:
    from cover_generator import CoverGenerator

try:
    from src.converters import HtmlConverter, EpubConverter, PdfConverter, MobiConverter
except ImportError:
    from converters import HtmlConverter, EpubConverter, PdfConverter, MobiConverter

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


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
        self.cover_path = self._discover_cover()
    
    def _discover_cover(self):
        """Try to find an existing cover in the output directory."""
        title = self.config.get('novel_title', 'Generated Novel')
        cover_filename = f"{title.replace(' ', '_')}_cover.png"
        potential_path = self.output_dir / cover_filename
        if potential_path.exists():
            print(f"Discovered existing cover at: {potential_path}")
            return str(potential_path)
        return None
    
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
            
        translations = {
            'English': {'by': 'By', 'generated_with': 'Generated with', 'toc': 'Table of Contents'},
            'Spanish': {'by': 'Por', 'generated_with': 'Generado con', 'toc': 'Índice'},
            'French': {'by': 'Par', 'generated_with': 'Généré con', 'toc': 'Table des matières'},
            'German': {'by': 'Von', 'generated_with': 'Generiert mit', 'toc': 'Inhaltsverzeichnis'},
            'Italian': {'by': 'Di', 'generated_with': 'Generato con', 'toc': 'Indice'},
            'Portuguese': {'by': 'Por', 'generated_with': 'Gerado com', 'toc': 'Índice'}
        }
        trans = translations.get(language, translations['English'])
        chapter_prefix = trans.get('chapter', 'Chapter')

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
            
            # Count scenes/sections in the outline to adjust sections_count dynamically
            outline_sections = [line for line in chapter_outline.split('\n') if line.startswith('## ')]
            current_sections_count = len(outline_sections) if outline_sections else sections_count
            
            # Get the chapter title from the outline or file name
            # If the first line of outline is # Chapter X: Title, use that
            first_line = chapter_outline.strip().split('\n')[0]
            if first_line.startswith('# '):
                raw_title = first_line.replace('# ', '').strip()
                if language != 'English':
                    # Ask AI to translate the chapter title if it's not in English (likely extracted from MD)
                    print(f"  - Requesting chapter title translation for: {raw_title}")
                    title_prompt = f"Translate this chapter title into {language}: '{raw_title}'. Return ONLY the translated title text, nothing else."
                    title_response = client.chat(
                        model=model_name,
                        messages=[{'role': 'user', 'content': title_prompt}]
                    )
                    if isinstance(title_response, dict):
                        chapter_header_title = title_response['message']['content'].strip().strip('"')
                    else:
                        chapter_header_title = title_response.message.content.strip().strip('"')
                else:
                    chapter_header_title = raw_title
            else:
                # Ask AI to generate/translate the chapter title in the target language
                print(f"  - Requesting chapter title translation for: {chapter_name}")
                title_prompt = f"Translate or generate a creative chapter title in {language} for a chapter with the filename '{chapter_name}'. Return ONLY the title text, nothing else."
                title_response = client.chat(
                    model=model_name,
                    messages=[{'role': 'user', 'content': title_prompt}]
                )
                if isinstance(title_response, dict):
                    chapter_header_title = title_response['message']['content'].strip().strip('"')
                else:
                    chapter_header_title = title_response.message.content.strip().strip('"')

            chapter_sections_content = []
            
            # Add chapter title as H1
            chapter_sections_content.append(f"# {chapter_header_title}")
            
            for section_num in range(1, current_sections_count + 1):
                print(f"  - Generating section {section_num} of {current_sections_count}...")
                
                previous_sections_context = ""
                if chapter_sections_content:
                    previous_sections_context = "\n\nContext from previous sections of this chapter:\n" + "\n\n".join(chapter_sections_content[-2:]) # Keep last 2 sections for context

                # Calculate words for this specific section
                current_words_per_section = min_words // current_sections_count

                # Get the section title from the outline if available
                current_section_title = f"Section {section_num}"
                if outline_sections and section_num <= len(outline_sections):
                    current_section_title = outline_sections[section_num-1].replace('## ', '').strip()

                prompt = f"""
                {context}
                
                Language: {language}
                
                Current Chapter Outline:
                {chapter_outline}
                
                {previous_sections_context}
                
                Instructions:
                1. Write section {section_num} of {current_sections_count} (Title: {current_section_title}) for this chapter in {language}.
                2. This section should have approximately {current_words_per_section} words.
                3. Maintain consistency with the provided Characters, Environment, and previous sections.
                4. DO NOT include any headers (like #, ##, or ###) in your response. The section title will be added automatically.
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
                
                # Clean up any potential AI-generated headers to maintain uniformity
                lines = section_content.strip().split('\n')
                cleaned_lines = []
                for line in lines:
                    if not line.strip().startswith('#'):
                        cleaned_lines.append(line)
                
                section_body = '\n'.join(cleaned_lines).strip()
                
                # Add a uniform header
                uniform_section_content = f"### {current_section_title}\n\n{section_body}"
                chapter_sections_content.append(uniform_section_content)
            
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
        
        # Enhanced description based on environmental documents if available
        description = self.config.get('cover_prompt', '')
        negative_prompt = self.config.get('negative_prompt', None)
        
        if not description:
            # 1. Try to get environment info
            if self.documents["environment"]:
                for env_doc in self.documents["environment"]:
                    with open(env_doc, 'r') as f:
                        description += f.read()[:100] + " "
            
            # 2. Try to get main character info
            if self.documents["characters"]:
                # Typically Elias in our examples
                with open(self.documents["characters"][0], 'r') as f:
                    description += f.read()[:100]
        
        description = description.replace('\n', ' ').strip()
        if not description:
            description = f"A book about {title}"
        
        cover_filename = f"{title.replace(' ', '_')}_cover.png"
        output_path = self.output_dir / cover_filename
        
        # Check if cover already exists
        if output_path.exists():
            print(f"Cover already exists at: {output_path}. Skipping generation.")
            self.cover_path = str(output_path)
            return self.cover_path
            
        # Generate the background image with 512x768 (standard portrait ratio)
        generated_path = self.cover_generator.generate_cover(
            title, 
            description, 
            output_path,
            width=512,
            height=768,
            negative_prompt=negative_prompt
        )
        
        language = self.config.get('language', 'English')
        if generated_path:
            # Add text to the generated image
            self._add_text_to_cover(generated_path, title, author, model, language)
            self.cover_path = generated_path
            
        return self.cover_path

    def _add_text_to_cover(self, image_path, title, author, model, language='English'):
        """Add title, author, and model text to the cover image."""
        try:
            translations = {
                'English': {'by': 'By', 'generated_with': 'Generated with'},
                'Spanish': {'by': 'Por', 'generated_with': 'Generado con'},
                'French': {'by': 'Par', 'generated_with': 'Généré con'},
                'German': {'by': 'Von', 'generated_with': 'Generiert mit'},
                'Italian': {'by': 'Di', 'generated_with': 'Generato con'},
                'Portuguese': {'by': 'Por', 'generated_with': 'Gerado com'}
            }
            trans = translations.get(language, translations['English'])
            
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
            # If title is too long, wrap it or scale it down
            max_title_width = width * 0.9
            current_font_size = int(height * 0.08)
            
            # Use font_paths[0] if it was found, otherwise fall back to default font
            selected_font_path = None
            for path in font_paths:
                if Path(path).exists():
                    selected_font_path = path
                    break

            # Initialize w and h to avoid "local variable 'w' referenced before assignment"
            w, h = 0, 0
            
            while current_font_size > 10:
                try:
                    if selected_font_path:
                        font_title = ImageFont.truetype(selected_font_path, current_font_size)
                    else:
                        font_title = ImageFont.load_default()
                except:
                    font_title = ImageFont.load_default()
                
                left, top, right, bottom = draw.textbbox((0, 0), title_text, font=font_title)
                w, h = right - left, bottom - top
                if w <= max_title_width or not selected_font_path:
                    break
                current_font_size -= 5

            draw.text(((width - w) / 2, height * 0.1), title_text, font=font_title, fill="white", stroke_width=2, stroke_fill="black")
            
            # Add Author (bottom-ish)
            author_text = f"{trans['by']} {author}"
            left, top, right, bottom = draw.textbbox((0, 0), author_text, font=font_author)
            w, h = right - left, bottom - top
            draw.text(((width - w) / 2, height * 0.8), author_text, font=font_author, fill="white", stroke_width=1, stroke_fill="black")
            
            # Add Model (bottom)
            model_text = f"{trans['generated_with']} {model}"
            left, top, right, bottom = draw.textbbox((0, 0), model_text, font=font_model)
            w, h = right - left, bottom - top
            draw.text(((width - w) / 2, height * 0.9), model_text, font=font_model, fill="lightgray", stroke_width=1, stroke_fill="black")
            
            img.save(image_path)
            print(f"Text added to cover: {image_path}")
        except Exception as e:
            print(f"Error adding text to cover: {str(e)}")

    def create_html(self, content, title="Generated Novel"):
        """Create a single HTML file from the content for debugging/preview"""
        converter = HtmlConverter(self.output_dir, self.config, self.cover_path)
        return converter.convert(content, title)

    def create_epub(self, content, title="Generated Novel"):
        """Create an EPUB file from the content with Table of Contents"""
        converter = EpubConverter(self.output_dir, self.config, self.cover_path)
        return converter.convert(content, title)

    def create_pdf(self, content, novel_title="Generated Novel"):
        """Create a PDF file from the content with Table of Contents"""
        converter = PdfConverter(self.output_dir, self.config, self.cover_path)
        return converter.convert(content, novel_title)

    def create_mobi(self, content, novel_title="Generated Novel"):
        """Create a MOBI file from the content using ebook-convert (Calibre)"""
        converter = MobiConverter(self.output_dir, self.config, self.cover_path)
        return converter.convert(content, novel_title)

    def save_output(self, content, filename):
        """Save generated content in the output folder with Markdown Table of Contents."""
        language = self.config.get('language', 'English')
        translations = {
            'English': {'toc': 'Table of Contents', 'credits': 'Credits', 'project_url': 'Project URL', 'created_at': 'Created at'},
            'Spanish': {'toc': 'Índice', 'credits': 'Créditos', 'project_url': 'URL del proyecto', 'created_at': 'Creado el'},
            'French': {'toc': 'Table des matières', 'credits': 'Crédits', 'project_url': 'URL du projet', 'created_at': 'Créé le'},
            'German': {'toc': 'Inhaltsverzeichnis', 'credits': 'Credits', 'project_url': 'Projekt-URL', 'created_at': 'Erstellt am'},
            'Italian': {'toc': 'Indice', 'credits': 'Crediti', 'project_url': 'URL del progetto', 'created_at': 'Creato il'},
            'Portuguese': {'toc': 'Índice', 'credits': 'Créditos', 'project_url': 'URL do projeto', 'created_at': 'Criado em'}
        }
        trans = translations.get(language, translations['English'])
        
        output_file = self.output_dir / filename
        try:
            # Include cover in Markdown if it exists
            if filename.endswith('.md'):
                novel_title = self.config.get('novel_title', 'Generated Novel')
                header = ""
                if self.cover_path:
                    cover_rel_path = Path(self.cover_path).name
                    header += f"![Cover]({cover_rel_path})\n\n"
                
                header += f"# {novel_title}\n\n"
                
                # Generate Markdown Table of Contents
                header += f"## {trans['toc']}\n\n"
                import re
                # Find all # titles
                # Standardize slug creation for TOC links
                def create_slug(text):
                    import re
                    import unicodedata
                    # Normalize and remove accents
                    nfkd_form = unicodedata.normalize('NFKD', text.lower())
                    only_ascii = nfkd_form.encode('ascii', 'ignore').decode('ascii')
                    # Keep alphanumeric and replace spaces with hyphens
                    slug = re.sub(r'[^a-z0-9]+', '-', only_ascii).strip('-')
                    return slug

                chapters = re.findall(r'^#\s+(.*)', content.strip(), flags=re.MULTILINE)
                for chapter in chapters:
                    if chapter == novel_title: # Skip if it's the main title
                        continue
                    # Create a slug for the link
                    slug = create_slug(chapter)
                    
                    # Also update the chapter headers in the content to include the anchor
                    content = re.sub(f"^# {re.escape(chapter)}$", f"# {chapter} <a name='{slug}'></a>", content, flags=re.MULTILINE)
                    
                    header += f"- [{chapter}](#{slug})\n"
                
                header += "\n---\n\n"
                content = header + content.strip()
                
                # Add Credits to Markdown
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                project_url = "https://github.com/RubenPozoMolina/novelaist"
                project_name = "Novelaist"
                project_version = "0.1.0"
                
                content += "\n\n---\n\n"
                content += f"## {trans['credits']}\n\n"
                content += f"- **{project_name} v{project_version}**\n"
                content += f"- **{trans['project_url']}:** {project_url}\n"
                content += f"- **{trans['created_at']}:** {timestamp}\n"
                
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
    novelaist.create_html(generated_content, title)
    novelaist.create_epub(generated_content, title)
    novelaist.create_pdf(generated_content, title)
    novelaist.create_mobi(generated_content, title)
    
    # Also save the original Markdown file
    markdown_filename = f"{title.replace(' ', '_')}.md"
    novelaist.save_output(generated_content, markdown_filename)
    
    print("Process completed successfully.")