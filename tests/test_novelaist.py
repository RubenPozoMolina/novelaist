import unittest
from pathlib import Path
import sys
import os

# Añadir el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from create_novel import Novelaist

class TestNovelaist(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.novelaist = Novelaist("examples/modern_messiah", "output_test")
    
    def test_load_documents(self):
        """Test para verificar la carga de documentos"""
        docs = self.novelaist.get_document_structure()
        self.assertIsNotNone(docs)
        self.assertIn("characters", docs)
        self.assertIn("chapters", docs)
        self.assertIn("environment", docs)
        
    def test_character_document_processing(self):
        """Test para verificar el procesamiento de documentos de personajes"""
        docs = self.novelaist.get_document_structure()
        if docs["characters"]:
            content = self.novelaist.process_character_document(docs["characters"][0])
            self.assertIsNotNone(content)
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 0)
    
    def test_chapter_document_processing(self):
        """Test para verificar el procesamiento de documentos de capítulos"""
        docs = self.novelaist.get_document_structure()
        if docs["chapters"]:
            content = self.novelaist.process_chapter_document(docs["chapters"][0])
            self.assertIsNotNone(content)
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 0)
    
    def test_generate_novel_content(self):
        """Test para verificar la generación de contenido"""
        content = self.novelaist.generate_novel_content()
        self.assertIsNotNone(content)
        self.assertIn("characters", content)
        self.assertIn("chapters", content)
        self.assertIn("environment", content)

if __name__ == '__main__':
    unittest.main()