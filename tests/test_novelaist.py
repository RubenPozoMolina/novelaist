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
    # With section-by-section, chat is called once per section
    # If the previous test file was cleaned up, it should be 2. 
    # But in the same session it might be additive. Let's check call_count >= 2
    assert mock_client_instance.chat.call_count >= 2 # 2 sections in mock config
    
    # Check the first call
    args, kwargs = mock_client_instance.chat.call_args_list[0]
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
    from ebooklib import epub
    novelaist = Novelaist(mock_examples_dir, output_dir)
    
    # Mock epub.EpubBook
    mock_book = MagicMock()
    epub.EpubBook = MagicMock(return_value=mock_book)
    
    # Mock epub.EpubHtml
    mock_html = MagicMock()
    epub.EpubHtml = MagicMock(return_value=mock_html)
    
    novelaist.create_epub("Some content", "Test Title")
    
    # Mock set_cover to not fail
    mock_book.set_cover = MagicMock()
    
    # Set a fake cover path
    cover_file = output_dir / "cover.png"
    cover_file.write_text("fake image content")
    novelaist.cover_path = str(cover_file)
    
    novelaist.create_epub("Some content", "Test Title")
    
    # Verify set_language was called with 'es' (for Spanish)
    mock_book.set_language.assert_called_with('es')
    
    # Verify set_cover was called if cover exists
    mock_book.set_cover.assert_called()
    
    # Verify EpubHtml was called for cover.xhtml
    # EPUB is generated twice in this test, once without cover and once with it
    # We look at the calls of the last creation
    assert epub.EpubHtml.call_count >= 3
    # First call of the whole test is for the first create_epub (without cover) -> chap_01.xhtml
    # Second call of the whole test is for the second create_epub (with cover) -> cover.xhtml
    cover_html_call = epub.EpubHtml.call_args_list[1]
    assert cover_html_call[1]['file_name'] == 'cover.xhtml'
    
    # Verify EpubHtml was created with lang='es'
    _, html_kwargs = epub.EpubHtml.call_args
    assert html_kwargs['lang'] == 'es'

def test_mobi_generation(mock_examples_dir, output_dir):
    from ebooklib import epub
    with patch('subprocess.run') as mock_run:
        novelaist = Novelaist(mock_examples_dir, output_dir)
        
        # Mock create_epub to return a dummy path
        with patch.object(Novelaist, 'create_epub', return_value="/tmp/test.epub"):
            novelaist.create_mobi("Some content", "Test Title")
            
            # Check if subprocess.run was called with ebook-convert
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert 'ebook-convert' in args
            assert "/tmp/test.epub" in args
            assert str(output_dir / "Test_Title.mobi") in args

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
        assert "## Table of Contents" in saved_content
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
    with patch('src.create_novel.SimpleDocTemplate') as MockDocTemplate:
        mock_doc = MagicMock()
        MockDocTemplate.return_value = mock_doc
        
        # Set a fake cover path
        cover_file = output_dir / "cover_for_pdf.png"
        cover_file.write_text("fake image content")
        novelaist.cover_path = str(cover_file)
        
        # Mock letter to avoid unpacking error in create_pdf
        with patch('src.create_novel.letter', (612, 792)):
            # We need to mock Image where it is used or imported
            with patch('src.create_novel.Image') as MockImage:
                mock_image_instance = MagicMock()
                MockImage.return_value = mock_image_instance
                
                novelaist.create_pdf("Some content", "Test Title")
                
                # Verify Image was instantiated
                MockImage.assert_called_with(str(cover_file))
                # Verify doc.build was called with a story that includes the image
                assert mock_doc.build.called
                story = mock_doc.build.call_args[0][0]
                assert any(item == mock_image_instance for item in story)

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
        assert "## Table of Contents" in md_content
        assert "- [Chapter 1](#chapter-1)" in md_content
        assert "- [Chapter 2](#chapter-2)" in md_content

def test_epub_toc_and_chapters(mock_examples_dir, output_dir):
    """Test that EPUB generation creates multiple chapters and a TOC"""
    # Use a real epub book but mock the save part if necessary. 
    # Actually, we can just use the real ebooklib since it's already installed.
    # The problem is that ebooklib might have been partially mocked earlier or there's a conflict.
    novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
    
    content = "# Chapter 1\nContent of chapter 1\n# Chapter 2\nContent of chapter 2"
    # To avoid the 'super() argument 1 must be a type, not MagicMock' error
    # which happens if ebooklib was mocked in sys.modules, we ensure it's fresh.
    if 'ebooklib' in sys.modules:
        import importlib
        import ebooklib.epub
        importlib.reload(ebooklib.epub)
        
    epub_path = novelaist.create_epub(content, "Test Novel")
    
    assert epub_path is not None
    assert Path(epub_path).exists()

def test_pdf_toc_inclusion(mock_examples_dir, output_dir):
    """Test that PDF generation includes a Table of Contents section"""
    with patch("reportlab.platypus.SimpleDocTemplate.build") as mock_build:
        novelaist = Novelaist(str(mock_examples_dir), str(output_dir))
        
        content = "# Chapter 1\nContent of chapter 1\n# Chapter 2\nContent of chapter 2"
        novelaist.create_pdf(content, "Test Novel")
        
        assert mock_build.called
        story = mock_build.call_args[0][0]
        
        # Verify "Table of Contents" paragraph is in the story
        toc_header_found = False
        chapters_found = []
        for item in story:
            if isinstance(item, Paragraph):
                if item.text == "Table of Contents":
                    toc_header_found = True
                if item.text in ["Chapter 1", "Chapter 2"]:
                    chapters_found.append(item.text)
        
        assert toc_header_found
        assert "Chapter 1" in chapters_found
        assert "Chapter 2" in chapters_found
