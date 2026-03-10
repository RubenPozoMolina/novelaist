# Novelaist - Proyecto de Escritura de Novelas con IA Local

## Descripción

Novelaist es una aplicación de escritura de novelas que utiliza modelos de IA local para crear novelas a partir de documentos markdown. El proyecto utiliza el modelo Command-R a través de Ollama para generar contenido literario basado en una estructura predefinida.

## Características

- Generación de novelas usando documentos markdown como base
- Soporte para múltiples formatos de salida (EPUB, MOBI, PDF)
- Integración con modelos de IA local (Command-R)
- Procesamiento de archivos markdown para extraer información
- Generación automática de contenido literario

## Estructura del Proyecto

```
novelaist/
├── examples/              # Ejemplos de documentos markdown
│   └── modern_messiah/
│       ├── characters/     # Documentos de personajes
│       ├── chapters/       # Documentos de capítulos
│       └── environment/    # Documentos de ambiente
├── src/                   # Código fuente principal
├── docs/                  # Documentación
└── tests/                 # Pruebas
```

## Requisitos

- Python 3.12
- Ollama instalado y ejecutándose
- Modelo Command-R descargado en Ollama

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual: `python3 -m venv .venv`
3. Activar entorno: `source .venv/bin/activate`
4. Instalar dependencias: `pip install ollama EbookLib reportlab Pillow markdown`
5. Asegurar que el modelo Command-R esté disponible en Ollama

## Uso

1. Crear documentos markdown en la estructura de ejemplo (en el directorio `examples/modern_messiah/`)
2. Ejecutar la aplicación con parámetros: `python src/create_novel.py <ruta_ejemplos> <ruta_salida>`
   - Ejemplo: `python src/create_novel.py examples/modern_messiah output/`
3. Ver el resultado en la carpeta de salida especificada
4. En una implementación completa, se exportaría el resultado en formatos EPUB, MOBI o PDF

## Ejemplos de documentos

Los documentos de ejemplo están organizados en:
- `examples/modern_messiah/characters/` - Documentos de personajes
- `examples/modern_messiah/chapters/` - Documentos de capítulos
- `examples/modern_messiah/environment/` - Documentos de ambiente

## Desarrollo

Para colaborar en el proyecto:

1. Crear un entorno virtual: `python3 -m venv .venv`
2. Activar entorno: `source .venv/bin/activate`
3. Instalar dependencias de desarrollo: `pip install -e .[dev]`
4. Ejecutar pruebas: `pytest`

## Licencia

Este proyecto está bajo la licencia MIT.