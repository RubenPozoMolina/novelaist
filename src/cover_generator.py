import torch
from diffusers import StableDiffusionPipeline
from pathlib import Path

class CoverGenerator:
    def __init__(self, model_id="Lykon/DreamShaper"):
        self.model_id = model_id
        self.pipeline = None

    def _load_pipeline(self):
        """Lazy load the pipeline to avoid heavy initialization if not needed."""
        if self.pipeline is None:
            print(f"Loading cover generation model: {self.model_id}...")
            # Use float16 for speed and lower memory usage if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device == "cuda" else torch.float32
            
            try:
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_id, 
                    torch_dtype=torch_dtype
                )
                self.pipeline.to(device)
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                raise

    def generate_cover(self, title, description, output_path, width=512, height=768, negative_prompt=None):
        """Generate a book cover based on the title and description."""
        self._load_pipeline()
        
        # We explicitly ask for no text in the generated image
        prompt = f"Professional book cover art for '{title}'. {description}. High quality, detailed, professional digital art, cinematic lighting, masterpiece"
        
        if negative_prompt is None:
            negative_prompt = "text, letters, words, watermark, signature, blurry, low quality, distorted, watermark, deformed, ugly, bad anatomy, poorly drawn face"
        
        print(f"Generating cover background for '{title}' ({width}x{height})...")
        try:
            # Use width and height for the generation
            image = self.pipeline(
                prompt=prompt, 
                negative_prompt=negative_prompt,
                width=width, 
                height=height,
                num_inference_steps=50,

            ).images[0]
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            image.save(output_file)
            print(f"Cover saved at: {output_file}")
            return str(output_file)
        except Exception as e:
            print(f"Error generating cover: {str(e)}")
            return None
