from pathlib import Path
import markdown
import os
import sys

class Novelaist:
    def __init__(self, examples_dir="examples", output_dir="output"):
        self.examples_dir = Path(examples_dir)
        self.output_dir = Path(output_dir)
        self.documents = {
            "characters": [],
            "chapters": [],
            "environment": []
        }
        self._load_documents()
    
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
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error al leer el documento: {str(e)}"
    
    def process_chapter_document(self, file_path):
        """Procesar un documento de capítulo"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error al leer el documento: {str(e)}"

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
        
        # Simular generación usando Command-R (en una implementación real esto se conectaría a Ollama)
        print("Simulación de generación con Command-R:")
        print("Utilizando documentos de personajes, capítulos y ambiente para generar contenido estructurado...")
        
        # Aquí se integraría el modelo Command-R de Ollama
        # Por ahora solo simulamos la salida estructurada
        return {
            "characters": character_info,
            "chapters": chapter_info,
            "environment": environment_info
        }

    def simulate_command_r_generation(self, prompt):
        """Simulación de generación con Command-R mediante Ollama (este método se conectará a Ollama en producción)"""
        # import ollama
        
        try:
            # En una implementación real, aquí se conectaría a Ollama
            # response = ollama.chat(model='command-r', messages=[{'role': 'user', 'content': prompt}])
            # return response.message.content
            
            # Simulación para demostración:
            return f"Simulación de respuesta de Command-R basada en el prompt:\n\n{prompt}\n\nEsta sería la salida real generada por Command-R procesando las instrucciones."
        
        except Exception as e:
            return f"Error al conectar con Command-R: {str(e)}"
    
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
    
    # Probar simulación de Command-R
    print("\n" + "="*50)
    prompt = "Escribe un capítulo de novela basado en los documentos de ejemplo"
    print("Simulación de generación con Command-R:")
    result = novelaist.simulate_command_r_generation(prompt)
    print(result)
    
    # Guardar resultado en archivo de salida
    print("\n" + "="*50)
    novelaist.save_output(result, "novela_generada.md")
    print("Proceso completado exitosamente.")