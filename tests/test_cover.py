import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock torch and diffusers
sys.modules['torch'] = MagicMock()
sys.modules['diffusers'] = MagicMock()

from src.cover_generator import CoverGenerator

def test_cover_generator_init():
    generator = CoverGenerator(model_id="test-model")
    assert generator.model_id == "test-model"
    assert generator.pipeline is None

@patch('src.cover_generator.StableDiffusionPipeline')
def test_generate_cover(mock_sd_pipeline, tmp_path):
    # Setup mocks
    mock_pipe = MagicMock()
    mock_sd_pipeline.from_pretrained.return_value = mock_pipe
    
    mock_image = MagicMock()
    mock_pipe.return_value.images = [mock_image]
    
    generator = CoverGenerator()
    output_path = tmp_path / "test_cover.png"
    
    # Run
    result = generator.generate_cover("Test Title", "Test Description", output_path)
    
    # Assert
    assert result == str(output_path)
    mock_sd_pipeline.from_pretrained.assert_called()
    assert mock_sd_pipeline.from_pretrained.call_args[0][0] == "Lykon/DreamShaper"
    mock_pipe.assert_called()
    # Check if prompt contains instructions for no text
    prompt = mock_pipe.call_args[1]['prompt']
    assert "no text" in prompt
    assert "no letters" in prompt
    assert "512" == str(mock_pipe.call_args[1]['width'])
    assert "768" == str(mock_pipe.call_args[1]['height'])
    mock_image.save.assert_called_with(output_path)

def test_cover_integration_in_novelaist(tmp_path):
    # Mock cover generator
    with patch('src.create_novel.CoverGenerator') as MockCoverGen:
        from src.create_novel import Novelaist
        
        # Setup mock examples dir
        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "config.json").write_text('{"novel_title": "Integrated Novel"}')
        (examples_dir / "characters").mkdir()
        (examples_dir / "chapters").mkdir()
        (examples_dir / "environment").mkdir()
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Mock generator instance
        mock_gen_instance = MockCoverGen.return_value
        mock_gen_instance.generate_cover.return_value = str(output_dir / "Integrated_Novel_cover.png")
        
        novelaist = Novelaist(examples_dir, output_dir)
        
        # Run cover generation
        cover_path = novelaist.generate_cover()
        
        assert cover_path == str(output_dir / "Integrated_Novel_cover.png")
        mock_gen_instance.generate_cover.assert_called()
        assert novelaist.cover_path == cover_path

def test_skip_cover_generation_if_exists(tmp_path):
    # Mock cover generator
    with patch('src.create_novel.CoverGenerator') as MockCoverGen:
        from src.create_novel import Novelaist
        
        # Setup mock examples dir
        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "config.json").write_text('{"novel_title": "Existing Cover"}')
        (examples_dir / "characters").mkdir()
        (examples_dir / "chapters").mkdir()
        (examples_dir / "environment").mkdir()
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create an existing cover file
        cover_file = output_dir / "Existing_Cover_cover.png"
        cover_file.write_text("fake image content")
        
        # Mock generator instance
        mock_gen_instance = MockCoverGen.return_value
        
        novelaist = Novelaist(examples_dir, output_dir)
        
        # Run cover generation
        cover_path = novelaist.generate_cover()
        
        # Assertions
        assert cover_path == str(cover_file)
        # generate_cover of CoverGenerator should NOT be called
        mock_gen_instance.generate_cover.assert_not_called()
        assert novelaist.cover_path == str(cover_file)

def test_add_text_to_cover(tmp_path):
    with patch('src.create_novel.CoverGenerator'):
        from src.create_novel import Novelaist
        from PIL import Image
        
        # Setup mock files
        examples_dir = tmp_path / "examples"
        examples_dir.mkdir()
        (examples_dir / "config.json").write_text('{"novel_title": "Text Novel", "author": "Author Name", "model": "Model X"}')
        (examples_dir / "characters").mkdir()
        (examples_dir / "chapters").mkdir()
        (examples_dir / "environment").mkdir()
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create a dummy image
        img_path = output_dir / "test_image.png"
        dummy_img = Image.new('RGB', (100, 100), color='red')
        dummy_img.save(img_path)
        
        novelaist = Novelaist(examples_dir, output_dir)
        
        # Mock PIL and its components to verify calls
        with patch('src.create_novel.PILImage.open') as mock_open:
            mock_img_instance = MagicMock()
            mock_open.return_value = mock_img_instance
            mock_img_instance.size = (100, 100)
            
            with patch('src.create_novel.ImageDraw.Draw') as mock_draw:
                mock_draw_instance = MagicMock()
                mock_draw.return_value = mock_draw_instance
                # Mock textbbox to return a dummy box
                mock_draw_instance.textbbox.return_value = (0, 0, 10, 10)
                
                novelaist._add_text_to_cover(str(img_path), "Title", "Author", "Model")
                
                # Check if text was drawn
                assert mock_draw_instance.text.call_count == 3
                # Verify title text was among the calls
                texts = [call[0][1] for call in mock_draw_instance.text.call_args_list]
                assert "TITLE" in texts
                assert "By Author" in texts
                assert "Generated with Model" in texts
                
                # Check if image was saved
                mock_img_instance.save.assert_called_with(str(img_path))
