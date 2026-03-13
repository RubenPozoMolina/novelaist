import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock heavy/external libraries
sys.modules['ollama'] = MagicMock()
sys.modules['ebooklib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.lib.styles'] = MagicMock()
sys.modules['reportlab.platypus'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['diffusers'] = MagicMock()

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
    assert mock_client_instance.chat.call_count == 2 # 2 sections in mock config
    
    # Check the first call
    args, kwargs = mock_client_instance.chat.call_args_list[0]
    prompt = kwargs['messages'][0]['content']
    assert "Spanish" in prompt
    assert "Write section 1 of 2" in prompt
    assert "approximately 250 words" in prompt # 500 / 2
    assert "Markdown formatting" in prompt

def test_skip_generation_if_chapter_exists(mock_examples_dir, output_dir):
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
        assert f.read() == generated_content

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
