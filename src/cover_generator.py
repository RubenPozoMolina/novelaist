import torch
import logging
from diffusers import StableDiffusionPipeline, FluxPipeline
from pathlib import Path

logger = logging.getLogger("novelaist.cover_generator")

class CoverGenerator:
    def __init__(self, model_id="Lykon/DreamShaper"):
        self.model_id = model_id
        self.pipeline = None

    def _load_pipeline(self):
        """Lazy load the pipeline to avoid heavy initialization if not needed."""
        if self.pipeline is None:
            logger.info(f"Loading cover generation model: {self.model_id}...")
            # Use float16 for speed and lower memory usage if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device == "cuda" else torch.float32
            
            try:
                if "flux" in self.model_id.lower():
                    logger.info("Using FluxPipeline for FLUX model")
                    self.pipeline = FluxPipeline.from_pretrained(
                        self.model_id,
                        torch_dtype=torch_dtype
                    )
                else:
                    self.pipeline = StableDiffusionPipeline.from_pretrained(
                        self.model_id, 
                        torch_dtype=torch_dtype
                    )
                self.pipeline.to(device)
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise

    def generate_cover(self, title, description, output_path, width=512, height=768, negative_prompt=None):
        """Generate a book cover based on the title and description."""
        self._load_pipeline()
        
        # We explicitly ask for no text in the generated image
        prompt = f"Professional book cover art for '{title}'. {description}. High quality, detailed, professional digital art, cinematic lighting, masterpiece, no text, no letters"
        
        is_flux = "flux" in self.model_id.lower()
        
        if negative_prompt is None and not is_flux:
            negative_prompt = "text, letters, words, watermark, signature, blurry, low quality, distorted, watermark, deformed, ugly, bad anatomy, poorly drawn face"
        
        logger.info(f"Generating cover background for '{title}' ({width}x{height}) using {self.model_id}...")
        try:
            # Use width and height for the generation
            if is_flux:
                # Flux usually doesn't take negative_prompt and uses guidance_scale differently
                image = self.pipeline(
                    prompt=prompt,
                    width=width,
                    height=height,
                    num_inference_steps=50,
                    guidance_scale=3.5,
                ).images[0]
            else:
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
            logger.info(f"Cover saved at: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error generating cover: {str(e)}")
            return None
