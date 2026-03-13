import argparse
import json
import ollama
from pathlib import Path

from ebooklib import epub
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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
        """Generate novel content based on loaded documents"""
        print("Generating novel content...")
        
        # Process documents to create prompts
        character_info = []
        chapter_info = []
        environment_info = []
        
        # Process characters
        for character_file in self.documents["characters"]:
            content = process_character_document(character_file)
            character_info.append(content)
        
        # Process chapters
        for chapter_file in self.documents["chapters"]:
            content = process_chapter_document(chapter_file)
            chapter_info.append(content)
        
        # Process environment
        for env_file in self.documents["environment"]:
            with open(env_file, 'r') as f:
                content = f.read()
            environment_info.append(content)
        
        # Create a prompt with information from documents
        language = self.config.get('language', 'English')
        prompt = f"""
        Write a novel in {language} based on the following information:
        
        Characters:
        {chr(10).join(character_info)}
        
        Chapters:
        {chr(10).join(chapter_info)}
        
        Environment:
        {chr(10).join(environment_info)}
        
        Novel title: {self.config.get('novel_title', 'Generated Novel')}
        Author: {self.config.get('author', 'Unknown Author')}
        Language: {language}
        
        Generate literary content consistent with this information in {language}.
        """
        
        # Generate content using the configured model
        model_name = self.config.get('model', 'command-r')
        host = self.config.get('host')
        
        if host:
            print(f"Connecting to {model_name} on {host}...")
            client = ollama.Client(host=host)
            response = client.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
        else:
            print(f"Connecting to {model_name}...")
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
        
        # In ollama-python 0.1.x, response is a dict with ['message']['content']
        if isinstance(response, dict):
            return response['message']['content']
        return response.message.content


    
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

            # Create chapter
            chapter = epub.EpubHtml(title='Introduction', file_name='chap_01.xhtml', lang=lang_code)
            chapter.content = f'<h1>{title}</h1>{formatted_content}'
            book.add_item(chapter)
            
            # Define style - ensure a readable serif font for novels
            style = 'BODY { font-family: "Times New Roman", Times, serif; line-height: 1.5; text-align: justify; }'
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)
            
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
        """Create a MOBI file from the content"""
        try:
            # For MOBI, we use the same logic as for EPUB since ebooklib supports export
            # in multiple formats. Here we use EPUB as a base and create an additional function
            # for converting to MOBI (requires Kindle or specific libraries)
            print("To create MOBI, kindle or additional libraries are needed.")
            # For now, we implement generation with EPUB, which is the first step
            epub_file = self.create_epub(content, novel_title)
            return epub_file  # We return the EPUB as an example
        except Exception as e:
            print(f"Error creating MOBI: {str(e)}")
            return None

    def save_output(self, content, filename):
        """Save generated content in the output folder"""
        output_file = self.output_dir / filename
        try:
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