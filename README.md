# Novelaist - Local AI Novel Writing Project

Novelaist is a tool that leverages local AI models to assist in the creative process of novel writing. By processing structured Markdown documents, it generates literary content that maintains consistency across characters, environments, and plot points.

## Features

- **Local AI Integration**: Uses the Command-R model via Ollama for private, offline content generation.
- **Structured Content Processing**: Automatically parses characters, chapters, and environment details from Markdown files.
- **Context-Aware Generation**: Maintains narrative consistency by feeding relevant metadata to the AI.
- **Multiple Output Formats**: Supports exporting the generated novel to EPUB, PDF, and MOBI (via EPUB conversion).
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

- **Python**: ^3.8.1
- **Poetry**: For dependency management.
- **Ollama**: Installed and running on your local machine.
- **Command-R Model**: Available in Ollama (`ollama pull command-r`).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/novelaist.git
   cd novelaist
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Verify Ollama**:
   Ensure Ollama is running and the Command-R model is downloaded:
   ```bash
   ollama list
   ```

## Usage

1. **Prepare your documents**: Organize your novel's Markdown files in the `examples/` directory following the established structure (see `Document Details` below).

2. **Run the generator**:
   ```bash
   poetry run python src/create_novel.py <project_path> <output_dir> [--model <model_name>] [--host <ollama_host>]
   ```
   *Example:*
   ```bash
   poetry run python src/create_novel.py examples/modern_messiah output/modern_messiah --model command-r --host http://localhost:11434
   ```

3. **Check the results**: The generated files (Markdown, EPUB, PDF) will be available in the specified output directory.

## Document Details

The project expects a specific folder structure to build the context for the AI:

- **`characters/`**: Detailed profiles for each character. Include personality traits, appearance, and background.
- **`chapters/`**: Outline for each chapter. Use headers for scenes to help the AI structure the narrative.
- **`environment/`**: Descriptions of locations, world rules, and key historical events.

## Development

To contribute or run tests:

1. **Install dev dependencies**:
   ```bash
   poetry install
   ```

2. **Run tests**:
   ```bash
   poetry run pytest
   ```

3. **Format code**:
   ```bash
   poetry run black .
   ```

## License

This project is licensed under the MIT License.
