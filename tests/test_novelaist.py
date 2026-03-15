import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock heavy/external libraries
sys.modules['ollama'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['diffusers'] = MagicMock()

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from src.create_novel import Novelaist
from src.converters import EpubConverter

@pytest.fixture
def mock_examples_dir(tmp_path):
    """Create a mock examples directory with a config.json"""
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    
    config = {
        "novel_title": "Test Novel",
        "author": "Test Author",
        "model": "test-model",
        "host": "http://test-host:11434",
        "language": "Spanish",
        "minimum_chapter_words_number": "500",
        "chapter_sections": 2
    }
    
    import json
    with open(examples_dir / "config.json", "w") as f:
        json.dump(config, f)
        
    # Create subdirectories to avoid load errors
    (examples_dir / "characters").mkdir()
    (examples_dir / "chapters").mkdir()
    (examples_dir / "environment").mkdir()
    
    return examples_dir

@pytest.fixture
def output_dir(tmp_path):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir

def test_novelaist_initialization(mock_examples_dir, output_dir):
    novelaist = Novelaist(mock_examples_dir, output_dir)
    assert novelaist.config["novel_title"] == "Test Novel"
    assert novelaist.config["author"] == "Test Author"
    assert novelaist.config["model"] == "test-model"
    assert novelaist.config["host"] == "http://test-host:11434"
    assert novelaist.config["language"] == "Spanish"

def test_language_and_constraints_in_prompt(mock_examples_dir, output_dir):
    import ollama
    # Create a dummy chapter file
    (mock_examples_dir / "chapters" / "001_intro.md").write_text("Chapter intro outline")
    
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock ollama.Client for host connections
    mock_client_instance = MagicMock()
    ollama.Client = MagicMock(return_value=mock_client_instance)
    
    # Mock response
    mock_response = {'message': {'content': 'Generated Chapter Content'}}
    mock_client_instance.chat.return_value = mock_response
    
    # Generate content
    novelaist.generate_novel_content()
        
    # Check if prompt contains the language and constraints
    # With section-by-section, chat is called once per section + once for chapter title
    assert mock_client_instance.chat.call_count >= 3 

    # Check the first call (now chapter title request)
    args, kwargs = mock_client_instance.chat.call_args_list[0]
    prompt = kwargs['messages'][0]['content']
    assert "Translate or generate a creative chapter title in Spanish" in prompt
        
    # Check the second call (now section 1)
    args, kwargs = mock_client_instance.chat.call_args_list[1]
    prompt = kwargs['messages'][0]['content']
    assert "Spanish" in prompt
    assert "Write section 1 of 2" in prompt
    assert "approximately 250 words" in prompt # 500 / 2
    assert "DO NOT include any headers" in prompt

def test_dynamic_section_count_from_outline(mock_examples_dir, output_dir):
    import ollama
    # Create a dummy chapter file with 3 scenes
    outline = "# Chapter 1\n\n## Scene 1\nContent 1\n## Scene 2\nContent 2\n## Scene 3\nContent 3"
    (mock_examples_dir / "chapters" / "001_dynamic.md").write_text(outline)
    
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock ollama.Client
    mock_client_instance = MagicMock()
    ollama.Client = MagicMock(return_value=mock_client_instance)
    
    # Mock response
    mock_response = {'message': {'content': 'Generated Section Content'}}
    mock_client_instance.chat.return_value = mock_response
    
    # Generate content
    novelaist.generate_novel_content()
    
    # Check if chat was called 3 times (for 3 scenes), ignoring the 2 calls from test_language_and_constraints_in_prompt if they were in the same session, but here it's a fresh run
    # Actually, generate_novel_content processes all files in chapters dir
    # So it will process 001_dynamic.md (3 sections) AND 001_intro.md (0 headers, fallback to 2 from config)
    # Total calls: 3 + 2 = 5 if both files exist. 
    # To be safe, let's look only at calls related to 001_dynamic
    
    # Get all prompts
    prompts = [call.kwargs['messages'][0]['content'] for call in mock_client_instance.chat.call_args_list]
    
    # Count how many prompts mention "section X of 3"
    dynamic_calls = [p for p in prompts if "of 3" in p]
    assert len(dynamic_calls) == 3
    
    # Check word count for 3 sections: 500 // 3 = 166
    assert "approximately 166 words" in dynamic_calls[0]
    assert "DO NOT include any headers" in dynamic_calls[0]

def test_uniform_section_headers(mock_examples_dir, output_dir):
    import ollama
    # Create a dummy chapter file with 2 scenes
    outline = "# Chapter 1\n\n## Scene A\nContent A\n## Scene B\nContent B"
    (mock_examples_dir / "chapters" / "001_uniform.md").write_text(outline)
    
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock ollama.Client
    mock_client_instance = MagicMock()
    ollama.Client = MagicMock(return_value=mock_client_instance)
    
    # Mock response with an unwanted header from AI
    # Section 1: Scene A
    # Section 2: Scene B
    mock_responses = [
        {'message': {'content': 'Translated Title'}}, # Title translation
        {'message': {'content': '### Scene A\nActual narrative for A'}},
        {'message': {'content': 'Actual narrative for B without header'}}
    ]
    mock_client_instance.chat.side_effect = mock_responses
    
    # Generate content
    content = novelaist.generate_novel_content()
    
    # Check generated file
    generated_file = output_dir / "001_uniform_generated.md"
    assert generated_file.exists()
    file_content = generated_file.read_text()
    
    # It should have exactly two ### headers, one for each scene title
    assert "### Scene A" in file_content
    assert "### Scene B" in file_content
    # And the AI's redundant header should be gone
    assert file_content.count("### Scene A") == 1
    assert "Actual narrative for A" in file_content
    assert "Actual narrative for B" in file_content

def test_caching_mechanism(mock_examples_dir, output_dir):
    import ollama
    # Create a dummy chapter file
    (mock_examples_dir / "chapters" / "001_intro.md").write_text("Chapter intro outline")
    
    # Create the generated chapter file beforehand
    existing_content = "Existing Chapter Content"
    (output_dir / "001_intro_generated.md").write_text(existing_content)
    
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock ollama.Client
    mock_client_instance = MagicMock()
    ollama.Client = MagicMock(return_value=mock_client_instance)
    
    # Generate content
    content = novelaist.generate_novel_content()
    
    # Verify ollama was NOT called
    mock_client_instance.chat.assert_not_called()
    assert existing_content in content

def test_epub_language(mock_examples_dir, output_dir):
    import xml2epub
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock xml2epub.Epub
    mock_book = MagicMock()
    # xml2epub.Epub is a class, we need to mock it where it's used or mock the module
    with patch('xml2epub.Epub', return_value=mock_book) as mock_epub_class, \
         patch('xml2epub.create_chapter_from_string') as mock_create_chapter, \
         patch('xml2epub.epub.get_cover_image'):
        
        # Configure Spanish in config
        novelaist.config['language'] = 'Spanish'
        
        content = "# Capítulo 1\nContenido"
        novelaist.create_epub(content, "Test Spanish")
        
        # Verify Epub was created with language='es'
        _, epub_kwargs = mock_epub_class.call_args
        assert epub_kwargs['language'] == 'es'
        
        # Verify translations are correctly set
        converter = EpubConverter(output_dir, novelaist.config)
        assert converter.translations['chapter'] == 'Capítulo'
        assert converter.translations['toc'] == 'Índice'


def test_markdown_filename_generation(mock_examples_dir, output_dir):
    novelaist = Novelaist(mock_examples_dir, output_dir)
    title = novelaist.config.get('novel_title', 'Generated Novel')
    
    # Simulate saving
    generated_content = "# Test Content"
    markdown_filename = f"{title.replace(' ', '_')}.md"
    novelaist.save_output(generated_content, markdown_filename)
    
    expected_path = output_dir / "Test_Novel.md"
    assert expected_path.exists()
    with open(expected_path, "r") as f:
        saved_content = f.read()
        assert "## Índice" in saved_content
        assert "# Test Content" in saved_content

def test_config_only_restriction(mock_examples_dir, output_dir):
    # Ensure Novelaist doesn't accept model/host anymore
    with pytest.raises(TypeError):
        Novelaist(mock_examples_dir, output_dir, model="illegal", host="illegal")

def test_document_loading(mock_examples_dir, output_dir):
    # Create some mock documents
    char_file = mock_examples_dir / "characters" / "char1.md"
    char_file.write_text("Character 1")
    
    chap_file = mock_examples_dir / "chapters" / "chap1.md"
    chap_file.write_text("Chapter 1")
    
    env_file = mock_examples_dir / "environment" / "env1.md"
    env_file.write_text("Env 1")
    
    novelaist = Novelaist(mock_examples_dir, output_dir)
    structure = novelaist.get_document_structure()
    
    assert len(structure["characters"]) == 1
    assert len(structure["chapters"]) == 1
    assert len(structure["environment"]) == 1
    assert structure["characters"][0].name == "char1.md"

def test_pdf_cover_inclusion(mock_examples_dir, output_dir):
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock reportlab classes
    with patch('src.converters.pdf_converter.SimpleDocTemplate') as MockDocTemplate:
        mock_doc = MagicMock()
        MockDocTemplate.return_value = mock_doc
        
        # Set a fake cover path
        cover_file = output_dir / "cover_for_pdf.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(cover_file)
        novelaist.cover_path = str(cover_file)
        
        # Mock Image in pdf_converter
        with patch('src.converters.pdf_converter.Image') as MockImage:
            novelaist.create_pdf("Some content", "Test Title")
            
            # Verify Image was instantiated
            MockImage.assert_called()
            # Verify doc.build was called
            assert mock_doc.build.called

def test_markdown_cover_inclusion(mock_examples_dir, output_dir):
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Set a fake cover path
    cover_file = output_dir / "cover_for_md.png"
    cover_file.write_text("fake image content")
    novelaist.cover_path = str(cover_file)
    
    content = "Main novel content"
    filename = "test.md"
    novelaist.save_output(content, filename)
    
    saved_file = output_dir / filename
    saved_content = saved_file.read_text()
    
    assert "![Cover](cover_for_md.png)" in saved_content
    assert content in saved_content

def test_html_generation(mock_examples_dir, output_dir):
    novelaist = Novelaist(mock_examples_dir, output_dir)
    title = "Test Novel"
    content = "# Chapter 1\nContent of chapter 1"
    
    html_path = novelaist.create_html(content, title)
    
    assert html_path is not None
    assert Path(html_path).exists()
    assert html_path.endswith(".html")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        assert "<title>Test Novel</title>" in html_content
        assert "<h1>Chapter 1</h1>" in html_content
        assert "<p>Content of chapter 1</p>" in html_content

def test_markdown_toc_generation(mock_examples_dir, output_dir):
    """Test that Markdown output includes a Table of Contents"""
    novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
    
    content = "# Chapter 1\nContent of chapter 1\n# Chapter 2\nContent of chapter 2"
    filename = "test_novel.md"
    
    novelaist.save_output(content, filename)
    
    output_path = output_dir / filename
    assert output_path.exists()
        
    with open(output_path, "r") as f:
        md_content = f.read()
        assert "## Índice" in md_content
        assert "- [Chapter 1](#chapter-1)" in md_content
        assert "- [Chapter 2](#chapter-2)" in md_content

def test_epub_toc_and_chapters(mock_examples_dir, output_dir):
    """Test that EPUB generation creates multiple chapters and a TOC"""
    novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
    
    content = "# Chapter 1\nContent of chapter 1\n# Chapter 2\nContent of chapter 2"
    
    epub_path = novelaist.create_epub(content, "Test Novel")
    
    assert epub_path is not None
    assert Path(epub_path).exists()

def test_epub_cover_verification(mock_examples_dir, output_dir):
    """Verifica que la portada existe correctamente dentro del archivo EPUB generado."""
    import zipfile
    from PIL import Image
    import os
    
    novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
    
    # Crear una portada real válida (PNG)
    cover_file = output_dir / "test_cover.png"
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(cover_file)
    novelaist.cover_path = str(cover_file)
    
    content = "# Capítulo 1\nContenido del capítulo 1"
    epub_path = novelaist.create_epub(content, "Novel With Cover")
    
    assert epub_path is not None
    assert Path(epub_path).exists()
    
    # Verificar el contenido del ZIP (EPUB)
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        
        # xml2epub hashes local images, so we check for presence of PNG in OEBPS/img/
        assert any(f.endswith(".png") and "OEBPS/img/" in f for f in file_list), f"La imagen de portada no está en el EPUB. Archivos: {file_list}"
        
        # Verificar que hay archivos xhtml para los capítulos
        assert any("0.xhtml" in f for f in file_list), "No se encontró el archivo del capítulo de portada"
        assert any("1.xhtml" in f for f in file_list), "No se encontró el archivo del primer capítulo"

def test_pdf_toc_inclusion(mock_examples_dir, output_dir):
    """Test that PDF generation includes a Table of Contents section"""
    with patch("reportlab.platypus.SimpleDocTemplate.build") as mock_build:
        novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
        
        content = "# Chapter 1\nContent of chapter 1\n# Chapter 2\nContent of chapter 2"
        novelaist.create_pdf(content, "Test Novel")
        
        assert mock_build.called
        story = mock_build.call_args[0][0]
        
        # Verify "Índice" paragraph is in the story
        toc_header_found = False
        chapters_found = []
        for item in story:
            if isinstance(item, Paragraph):
                if item.text == "Índice":
                    toc_header_found = True
                if item.text in ["Chapter 1", "Chapter 2"]:
                    chapters_found.append(item.text)
        
        assert toc_header_found
        assert "Chapter 1" in chapters_found
        assert "Chapter 2" in chapters_found
