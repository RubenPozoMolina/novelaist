from abc import ABC, abstractmethod
from pathlib import Path

class BaseConverter(ABC):
    def __init__(self, output_dir, config, cover_path=None):
        self.output_dir = Path(output_dir)
        self.config = config
        self.cover_path = cover_path
        self.language = self.config.get('language', 'English')
        self.translations = self._get_translations()

    def _get_translations(self):
        translations = {
            'English': {
                'toc': 'Table of Contents',
                'introduction': 'Introduction',
                'chapter': 'Chapter',
                'author': 'Author',
                'by': 'By',
                'date': 'Date',
                'generated_with': 'Generated with',
                'cover': 'Cover',
                'credits': 'Credits',
                'project_url': 'Project URL',
                'created_at': 'Created at'
            },
            'Spanish': {
                'toc': 'Índice',
                'introduction': 'Introducción',
                'chapter': 'Capítulo',
                'author': 'Autor',
                'by': 'Por',
                'date': 'Fecha',
                'generated_with': 'Generado con',
                'cover': 'Portada',
                'credits': 'Créditos',
                'project_url': 'URL del proyecto',
                'created_at': 'Creado el'
            },
            'French': {
                'toc': 'Table des matières',
                'introduction': 'Introduction',
                'chapter': 'Chapitre',
                'author': 'Auteur',
                'by': 'Par',
                'date': 'Date',
                'generated_with': 'Généré con',
                'cover': 'Couverture',
                'credits': 'Crédits',
                'project_url': 'URL du projet',
                'created_at': 'Créé le'
            },
            'German': {
                'toc': 'Inhaltsverzeichnis',
                'introduction': 'Einleitung',
                'chapter': 'Kapitel',
                'author': 'Autor',
                'by': 'Von',
                'date': 'Datum',
                'generated_with': 'Generiert mit',
                'cover': 'Cover',
                'credits': 'Credits',
                'project_url': 'Projekt-URL',
                'created_at': 'Erstellt am'
            },
            'Italian': {
                'toc': 'Indice',
                'introduction': 'Introduzione',
                'chapter': 'Capitolo',
                'author': 'Autore',
                'by': 'Di',
                'date': 'Data',
                'generated_with': 'Generato con',
                'cover': 'Copertina',
                'credits': 'Crediti',
                'project_url': 'URL del progetto',
                'created_at': 'Creato il'
            },
            'Portuguese': {
                'toc': 'Índice',
                'introduction': 'Introdução',
                'chapter': 'Capítulo',
                'author': 'Autor',
                'by': 'Por',
                'date': 'Data',
                'generated_with': 'Gerado com',
                'cover': 'Capa',
                'credits': 'Créditos',
                'project_url': 'URL do projeto',
                'created_at': 'Criado em'
            }
        }
        return translations.get(self.language, translations['English'])

    @abstractmethod
    def convert(self, content, title):
        pass
