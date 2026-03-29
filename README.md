# Novelaist - AI Novel Writing Project

Novelaist is a tool that leverages AI models (local via Ollama or cloud via Anthropic Claude) to assist in the creative process of novel writing. By processing structured Markdown documents, it generates literary content that maintains consistency across characters, environments, and plot points.

## Features

- **Multi-Provider AI Integration**: Supports both local AI via [Ollama](https://ollama.com/) and cloud AI via [Anthropic Claude](https://www.anthropic.com/claude).
- **Structured Content Processing**: Automatically parses characters, chapters, and environment details from Markdown files.
- **Context-Aware Generation**: Maintains narrative consistency by feeding relevant metadata to the AI.
- **Multiple Output Formats**: Supports exporting the generated novel to EPUB, PDF, and HTML.
- **Credits Section**: Every output file includes a credits section with the generation timestamp and configuration used (sensitive fields are excluded automatically).
- **Customizable Cover Typography**: Font, size, and color for cover text are fully configurable via `config.json`.
- **Log to File**: Use `--log` to save the full generation log to a file for later review.
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
- **Ollama** OR **Anthropic API Key**: Choose your AI provider:
  - **Ollama**: For local, offline AI generation.
  - **Anthropic Claude**: For cloud-based AI with higher quality models.
- **Cuda (Optional)**: Recommended for faster cover generation with Stable Diffusion.

## Installation

### 1. External Dependencies

#### Option A: Ollama (Local AI)
Download and install from [ollama.com](https://ollama.com/). After installing, pull the model used in the examples:
```bash
ollama pull llama3
```

#### Option B: Anthropic Claude (Cloud AI)
1. Create an account at [anthropic.com](https://www.anthropic.com/)
2. Get your API key from the [console](https://console.anthropic.com/)
3. Set your API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

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
   *Note: Edit `config.json` to set your preferred model, provider, and optional parameters.*

4. **Verify your AI provider**:

   **For Ollama:**
   ```bash
   ollama list
   ```

   **For Anthropic:**
   ```bash
   # Test your API key is set
   echo $ANTHROPIC_API_KEY
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

   **Optional: Save log to a file** using the `--log` parameter:
   ```bash
   poetry run python src/create_novel.py examples/modern_messiah output/modern_messiah --log output/modern_messiah/run.log
   ```

3. **Check the results**: The generated files (Markdown, EPUB, PDF, HTML) will be available in the specified output directory. Each output file includes a **credits section** with the generation timestamp and the configuration parameters used (sensitive fields like `api_key` and `host` are automatically excluded).

## AI Provider Configuration

### Using Ollama (Local AI)

```json
{
    "novel_title": "My Novel",
    "author": "Your Name",
    "provider": "ollama",
    "model": "llama3",
    "host": "http://localhost:11434",
    "source_language": "English",
    "target_language": "English",
    "minimum_chapter_words_number": "1000",
    "chapter_sections": 3,
    "cover_model": "Lykon/DreamShaper",
    "cover_prompt": "An oil painting of a futuristic city...",
    "cover_negative_prompt": "cartoon, anime, watermark, text",
    "cover_font": "/path/to/font.ttf",
    "cover_font_size_title": 0.08,
    "cover_font_size_author": 0.04,
    "cover_font_size_model": 0.02,
    "cover_font_color_title": "white",
    "cover_font_color_author": "white",
    "cover_font_color_model": "lightgray"
}
```

### Using Anthropic Claude (Cloud AI)

```json
{
    "novel_title": "My Novel",
    "author": "Your Name",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "api_key": "your-api-key-here",
    "source_language": "English",
    "target_language": "English",
    "minimum_chapter_words_number": "1000",
    "chapter_sections": 3,
    "cover_model": "Lykon/DreamShaper",
    "cover_prompt": "An oil painting of a futuristic city...",
    "cover_negative_prompt": "cartoon, anime, watermark, text",
    "cover_font": "/path/to/font.ttf",
    "cover_font_size_title": 0.08,
    "cover_font_size_author": 0.04,
    "cover_font_size_model": 0.02,
    "cover_font_color_title": "white",
    "cover_font_color_author": "white",
    "cover_font_color_model": "lightgray"
}
```

**Available Claude Models:**
- `claude-3-5-sonnet-20241022` - Most intelligent, best for most tasks
- `claude-3-5-haiku-20241022` - Fastest and most cost-effective
- `claude-3-opus-20240229` - Most powerful legacy model, best for complex reasoning tasks
- `claude-3-sonnet-20240229` - Balanced legacy model
- `claude-3-haiku-20240307` - Fastest legacy model

**Note:** You can also set the API key via environment variable `ANTHROPIC_API_KEY` instead of in the config file.

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
- **`provider`**: The AI provider to use (`ollama` or `anthropic`).
- **`model`**: The AI model to use (e.g., `llama3`, `claude-3-5-sonnet-20241022`).
- **`host`**: (Ollama only) The host URL for Ollama (e.g., `http://localhost:11434`).
- **`api_key`**: (Anthropic only) Your Anthropic API key.
- **`source_language`**: The source language of the original documents (e.g., `Spanish`, `English`). Default: `English`.
- **`target_language`**: The language for the generated content and translation (e.g., `Spanish`, `English`). Default: same as `source_language`.
- **`minimum_chapter_words_number`**: Target word count for each chapter.
- **`chapter_sections`**: Default number of sections to split a chapter into if no `##` headers are found in the chapter outline. If `##` headers are present, they take precedence.
- **`cover_model`**: Model used for cover generation.
- **`cover_prompt`**: Prompt for the cover image.
- **`cover_negative_prompt`**: Negative prompt for the cover image.
- **`cover_font`**: (Optional) Path to a `.ttf` font file for the cover text. Defaults to DejaVuSans-Bold or Liberation Sans if available.
- **`cover_font_size_title`**: (Optional) Title font size as a ratio of the image height (e.g., `0.08` = 8%). Default: `0.08`.
- **`cover_font_size_author`**: (Optional) Author font size as a ratio of the image height. Default: `0.04`.
- **`cover_font_size_model`**: (Optional) Model label font size as a ratio of the image height. Default: `0.02`.
- **`cover_font_color_title`**: (Optional) Color for the title text (PIL color name or hex). Default: `"white"`.
- **`cover_font_color_author`**: (Optional) Color for the author text. Default: `"white"`.
- **`cover_font_color_model`**: (Optional) Color for the model label text. Default: `"lightgray"`.

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

This project uses two types of licenses to distinguish between software and creative content:

### Software (Novelaist)
The source code for **Novelaist** is under the **MIT** license. This allows for free use, copying, modification, and distribution of the software, provided the original copyright notice is included. See the [LICENSE](LICENSE) file for more details.

### Content (Modern Messiah)
The literary content, characters, plots, and universes that make up the **Modern Messiah** example (located in `examples/modern_messiah/`) are protected under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license.

This means you are free to:
- **Share**: Copy and redistribute the material in any medium or format.
- **Adapt**: Remix, transform, and build upon the material for any purpose, even commercially.

Under the following terms:
- **Attribution**: You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- **ShareAlike**: If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

See the [LICENSE_MODERN_MESSIAH.md](LICENSE_MODERN_MESSIAH.md) file for a summary of the license or visit [Creative Commons](https://creativecommons.org/licenses/by-sa/4.0/) for the full legal text.
