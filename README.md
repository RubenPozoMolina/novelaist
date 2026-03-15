# Novelaist - Local AI Novel Writing Project

Novelaist is a tool that leverages local AI models to assist in the creative process of novel writing. By processing structured Markdown documents, it generates literary content that maintains consistency across characters, environments, and plot points.

## Features

- **Local AI Integration**: Uses the Llama3 model via Ollama for private, offline content generation.
- **Structured Content Processing**: Automatically parses characters, chapters, and environment details from Markdown files.
- **Context-Aware Generation**: Maintains narrative consistency by feeding relevant metadata to the AI.
- **Multiple Output Formats**: Supports exporting the generated novel to EPUB, PDF, and HTML.
- **Extensible Architecture**: Easy to add new document types or change the underlying AI model.

## Project Structure

```text
novelaist/
├── examples/              # Sample novel projects
│   └── modern_messiah/    # "Modern Messiah" example project
│       ├── characters/     # Character profiles (.md)
│       ├── chapters/       # Plot outlines and scenes (.md)
│       └── environment/    # World-building and events (.md)
├── src/                   # Source code
│   └── create_novel.py    # Main entry point
├── docs/                  # Documentation
└── tests/                 # Unit and integration tests
```

## Requirements

- **Python**: ^3.12 (specifically tested on 3.12.3)
- **Poetry**: For Python dependency management.
- **Ollama**: Installed and running on your local machine for text generation.
- **Cuda (Optional)**: Recommended for faster cover generation with Stable Diffusion.

## Installation

### 1. External Dependencies

#### Ollama
Download and install from [ollama.com](https://ollama.com/). After installing, pull the model used in the examples:
```bash
ollama pull llama3
```
*(Note: You can change the model in the project's `config.json`)*

### 2. Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/RubenPozoMolina/novelaist.git
   cd novelaist
   ```

2. **Install Python dependencies**:

   #### Option A: Using Poetry (Recommended)
   ```bash
   poetry install
   ```
   *Note: If you have issues with `torch` or `diffusers`, ensure you have a compatible Cuda environment or install the CPU versions manually.*

   #### Option B: Using Pip (Manual Installation)
   If you don't want to use Poetry, you can install the dependencies using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare configuration**:
   Copy the example configuration file to `config.json` inside your project directory:
   ```bash
   cp examples/modern_messiah/config.json.template examples/modern_messiah/config.json
   ```
   *Note: Edit `config.json` to set your preferred model, Ollama host, and optional parameters like `cover_prompt` or `negative_prompt`.*

4. **Verify Ollama**:
   Ensure Ollama is running and the Llama3 model is downloaded:
   ```bash
   ollama list
   ```

## Usage

1. **Prepare your documents**: Organize your novel's Markdown files in the `examples/` directory following the established structure (see `Document Details` below).

2. **Run the generator**:

   **Using Poetry:**
   ```bash
   poetry run python src/create_novel.py <project_path> <output_dir>
   ```

   **Using Pip:**
   ```bash
   python src/create_novel.py <project_path> <output_dir>
   ```

   *Example (Poetry):*
   ```bash
   poetry run python src/create_novel.py examples/modern_messiah output/modern_messiah
   ```

3. **Check the results**: The generated files (Markdown, EPUB, PDF, HTML) will be available in the specified output directory.

## Troubleshooting

If you encounter an error like:
`RuntimeError: html5-parser and lxml are using different versions of libxml2.`

This usually happens when `lxml` is installed from a binary wheel that conflicts with another library using a different version of `libxml2`. To fix it, reinstall `lxml` by compiling it from source:

```bash
pip install --no-binary lxml lxml
```
*Note: This may require development tools (like `gcc`, `libxml2-dev`, and `libxslt-dev`) to be installed on your system.*

## Document Details

The project expects a specific folder structure to build the context for the AI:

- **`characters/`**: Detailed profiles for each character. Include personality traits, appearance, and background.
- **`chapters/`**: Outline for each chapter. Use headers (`##`) for scenes to help the AI structure the narrative. Note that the number of `##` headers in each chapter file will override the `chapter_sections` parameter in `config.json` for that specific chapter, allowing for dynamic chapter lengths.
- **`environment/`**: Descriptions of locations, world rules, and key historical events.

## Configuration

You can customize the generation process by editing the `config.json` file in your project directory:

- **`novel_title`**: The title of your novel.
- **`author`**: The author's name.
- **`model`**: The AI model to use (e.g., `llama3`).
- **`language`**: The language for the generated content (e.g., `Spanish`, `English`).
- **`minimum_chapter_words_number`**: Target word count for each chapter.
- **`chapter_sections`**: Default number of sections to split a chapter into if no `##` headers are found in the chapter outline. If `##` headers are present, they take precedence.
- **`cover_model`**: Model used for cover generation.
- **`cover_prompt`**: Prompt for the cover image.
- **`cover_negative_prompt`**: Negative prompt for the cover image.

## Development

To contribute or run tests:

1. **Install dev dependencies**:
   - **Poetry**: `poetry install`
   - **Pip**: `pip install -r requirements.txt`

2. **Run tests**:
   - **Poetry**: `poetry run pytest`
   - **Pip**: `pytest`

3. **Format code**:
   - **Poetry**: `poetry run black .`
   - **Pip**: `black .`

## License

Este proyecto utiliza dos tipos de licencias para distinguir entre el software y el contenido creativo:

### Software (Novelaist)
El código fuente de **Novelaist** está bajo la licencia **MIT**. Esto permite el uso, copia, modificación y distribución gratuita del software, siempre que se incluya el aviso de copyright original. Consulta el archivo [LICENSE](LICENSE) para más detalles.

### Contenido (Modern Messiah)
El contenido literario, personajes, tramas y universos que componen el ejemplo **Modern Messiah** (ubicado en `examples/modern_messiah/`) están protegidos bajo la licencia **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**. 

Esto significa que eres libre de:
- **Compartir**: Copiar y redistribuir el material en cualquier medio o formato.
- **Adaptar**: Mezclar, transformar y construir sobre el material para cualquier propósito, incluso comercial.

Bajo los siguientes términos:
- **Atribución**: Debes dar crédito de manera adecuada, proporcionar un enlace a la licencia e indicar si se han realizado cambios.
- **Compartir Igual**: Si remezclas, transformas o creas a partir del material, debes distribuir tus contribuciones bajo la misma licencia que el original.

Consulta el archivo [LICENSE_MODERN_MESSIAH.md](LICENSE_MODERN_MESSIAH.md) para el resumen de la licencia o visita [Creative Commons](https://creativecommons.org/licenses/by-sa/4.0/) para el texto legal completo.
