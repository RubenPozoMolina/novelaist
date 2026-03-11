from pathlib import Path
import markdown
import os
import sys
import json
from ebooklib import epub
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image

class Novelaist:
    def __init__(self, examples_dir="examples", output_dir="output"):
        self.examples_dir = Path(examples_dir)
        self.output_dir = Path(output_dir)
        self.config = self._load_config()
        self.documents = {
            "characters": [],
            "chapters": [],
            "environment": []
        }
        self._load_documents()
    
    def _load_config(self):
        """Cargar configuración desde el archivo config.json"""
        config_path = self.examples_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar config.json: {str(e)}")
                return {}
        return {}
    
    def _load_documents(self):
        """Cargar documentos de ejemplo desde el directorio de ejemplos"""
        # Cargar documentos de personajes
        characters_dir = self.examples_dir / "characters"
        if characters_dir.exists():
            for file in characters_dir.glob("*.md"):
                self.documents["characters"].append(file)
        
        # Cargar documentos de capítulos
        chapters_dir = self.examples_dir / "chapters"
        if chapters_dir.exists():
            for file in chapters_dir.glob("*.md"):
                self.documents["chapters"].append(file)
        
        # Cargar documentos de ambiente
        environment_dir = self.examples_dir / "environment"
        if environment_dir.exists():
            for file in environment_dir.glob("*.md"):
                self.documents["environment"].append(file)
    
    def get_document_structure(self):
        """Obtener la estructura de documentos cargados"""
        return self.documents
    
    def process_character_document(self, file_path):
        """Procesar un documento de personaje"""
        with open(file_path, 'r') as f:
            content = f.read()
        return content
    
    def process_chapter_document(self, file_path):
        """Procesar un documento de capítulo"""
        with open(file_path, 'r') as f:
            content = f.read()
        return content

    def generate_novel_content(self):
        """Generar contenido de novela basado en los documentos cargados"""
        print("Generando contenido de novela...")
        
        # Procesar documentos para crear prompts
        character_info = []
        chapter_info = []
        environment_info = []
        
        # Procesar personajes
        for character_file in self.documents["characters"]:
            content = self.process_character_document(character_file)
            character_info.append(content)
        
        # Procesar capítulos
        for chapter_file in self.documents["chapters"]:
            content = self.process_chapter_document(chapter_file)
            chapter_info.append(content)
        
        # Procesar ambiente
        for env_file in self.documents["environment"]:
            with open(env_file, 'r') as f:
                content = f.read()
            environment_info.append(content)
        
        # Crear prompt con la información de los documentos
        prompt = f"""
        Escribe una novela basada en la siguiente información:
        
        Personajes:
        {chr(10).join(character_info)}
        
        Capítulos:
        {chr(10).join(chapter_info)}
        
        Ambiente:
        {chr(10).join(environment_info)}
        
        Título de la novela: {self.config.get('novel_title', 'Novela Generada')}
        Autor: {self.config.get('author', 'Autor Desconocido')}
        
        Genera un contenido literario coherente con esta información.
        """
        
        # Generar contenido usando Command-R
        print("Conectando con Command-R...")
        
        # Aquí se integraría el modelo Command-R de Ollama
        import ollama
        
        response = ollama.chat(model=self.config.get('model', 'command-r'), messages=[{'role': 'user', 'content': prompt}])
        return response.message.content


    
    def create_epub(self, content, title="Novela Generada"):
        """Crear un archivo EPUB a partir del contenido"""
        try:
            book = epub.EpubBook()
            book.set_identifier('id123456')
            book.set_title(title)
            book.set_language('es')
            
            # Usar configuración del autor si está disponible
            author = self.config.get('author', 'Autor Desconocido')
            book.add_author(author)
            
            # Crear capítulo
            chapter = epub.EpubHtml(title='Introducción', file_name='chap_01.xhtml', lang='es')
            chapter.content = f'<h1>{title}</h1><p>{content}</p>'
            book.add_item(chapter)
            
            # Definir estilo
            style = 'BODY { font-family: Arial, sans-serif; }'
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)
            
            # Generar tabla de contenidos
            book.toc = [epub.Link('chap_01.xhtml', title, 'intro')]
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Aplicar estilo
            book.spine = ['nav', chapter]
            
            # Guardar archivo
            filename = self.output_dir / f"{title.replace(' ', '_')}.epub"
            epub.write_epub(filename, book, {})
            print(f"Archivo EPUB guardado en: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error al crear EPUB: {str(e)}")
            return None

    def create_pdf(self, content, title="Novela Generada"):
        """Crear un archivo PDF a partir del contenido"""
        try:
            filename = self.output_dir / f"{title.replace(' ', '_')}.pdf"
            doc = SimpleDocTemplate(str(filename), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_para = Paragraph(title, styles['Title'])
            story.append(title_para)
            story.append(Spacer(1, 12))
            
            # Autor
            author_para = Paragraph(f"Autor: {self.config.get('author', 'Autor Desconocido')}", styles['Normal'])
            story.append(author_para)
            story.append(Spacer(1, 12))
            
            # Fecha
            date_para = Paragraph(f"Fecha: {self.config.get('date', '')}", styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 12))
            
            # Contenido
            content_para = Paragraph(content, styles['Normal'])
            story.append(content_para)
            
            doc.build(story)
            print(f"Archivo PDF guardado en: {filename}")
            return str(filename)
        except Exception as e:
            print(f"Error al crear PDF: {str(e)}")
            return None

    def create_mobi(self, content, title="Novela Generada"):
        """Crear un archivo MOBI a partir del contenido"""
        try:
            # Para MOBI, usamos la misma lógica que para EPUB ya que ebooklib soporta exportación
            # en múltiples formatos. Aquí usamos EPUB como base y creamos una función adicional
            # para convertir a MOBI (requiere kindlegen o bibliotecas específicas)
            print("Para crear MOBI se necesita kindlegen o librerías adicionales.")
            # Para ahora implementamos la generación con EPUB que es el primer paso
            epub_file = self.create_epub(content, title)
            return epub_file  # Devolvemos el EPUB como ejemplo
        except Exception as e:
            print(f"Error al crear MOBI: {str(e)}")
            return None

    def save_output(self, content, filename):
        """Guardar el contenido generado en la carpeta de salida"""
        self.output_dir.mkdir(exist_ok=True)
        output_file = self.output_dir / filename
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"Contenido guardado en: {output_file}")
        except Exception as e:
            print(f"Error al guardar el archivo: {str(e)}")

if __name__ == "__main__":
    # Procesar parámetros de entrada
    if len(sys.argv) < 3:
        print("Uso: python src/novelaist_core.py <ruta_ejemplos> <ruta_salida>")
        print("Ejemplo: python src/novelaist_core.py examples/modern_messiah output/")
        sys.exit(1)
    
    examples_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Crear instancia de Novelaist con parámetros de entrada
    novelaist = Novelaist(examples_dir, output_dir)
    
    # Mostrar estructura de documentos
    print("Estructura de documentos:")
    docs = novelaist.get_document_structure()
    for category, files in docs.items():
        print(f"  {category}: {len(files)} archivos")
        for file in files:
            print(f"    - {file.name}")
    
    # Probar procesamiento de un documento
    if docs["characters"]:
        print("\nContenido de primer documento de personaje:")
        print(novelaist.process_character_document(docs["characters"][0]))
    
    # Probar generación
    print("\n" + "="*50)
    generated_content = novelaist.generate_novel_content()
    print("Generación completada.")
    
    # Guardar resultado en archivos de salida
    print("\n" + "="*50)
    print("Generando archivos en formatos EPUB, MOBI y PDF...")
    
    # Crear los archivos en diferentes formatos
    novelaist.create_epub(generated_content, "Novela_Generada")
    novelaist.create_pdf(generated_content, "Novela_Generada")
    novelaist.create_mobi(generated_content, "Novela_Generada")
    
    # Guardar también el archivo markdown original
    novelaist.save_output(generated_content, "novela_generada.md")
    
    print("Proceso completado exitosamente.")