import os
import torch
import time
import random
from PIL import Image

class ImageService:
    """Service for generating images using Stable Diffusion"""
    
    def __init__(self):
        """Initialize image service"""
        # Create output directory
        os.makedirs("output/images", exist_ok=True)
        
        # Initialize Stable Diffusion (lazy loading)
        self.sd_pipeline = None
    
    def initialize_stable_diffusion(self):
        """Initialize Stable Diffusion XL pipeline"""
        try:
            from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
            
            # Load SDXL model
            self.sd_pipeline = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                variant="fp16" if torch.cuda.is_available() else None,
                use_safetensors=True
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.sd_pipeline = self.sd_pipeline.to("cuda")
            
            # Set optimal scheduler
            self.sd_pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.sd_pipeline.scheduler.config,
                algorithm_type="sde-dpmsolver++",
                use_karras_sigmas=True
            )
            
            return True
        except ImportError:
            print("Diffusers library not available. Please install it first.")
            return False
    
    def generate_image(self, prompt, width=1024, height=680):
        """Generate a single image using Stable Diffusion"""
        # Initialize SD if not already done
        if self.sd_pipeline is None:
            success = self.initialize_stable_diffusion()
            if not success:
                return None
        
        # Create a more refined negative prompt based on best practices
        negative_prompt = (
            "low quality, blurry, distorted, deformed, disfigured, bad anatomy, "
            "bad proportions, extra limbs, missing limbs, disconnected limbs, "
            "duplicate, mutated, ugly, watermark, watermarked, text, signature, "
            "logo, oversaturated, cartoon, 3d render, bad art, amateur, "
            "poorly drawn face, poorly drawn hands, poorly drawn feet"
        )
        
        # Generate a random seed for variety but allow reproducibility
        seed = random.randint(1, 2147483647)
        torch_generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)
        
        # Generate image
        try:
            image = self.sd_pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=40,     # Higher step count for better quality
                guidance_scale=7.5,         # Optimal CFG value for SDXL
                generator=torch_generator,
                output_type="pil"
            ).images[0]
            
            return image, seed
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None, None
    
    def generate_story_images(self, image_prompts):
        """Generate images for all prompts"""
        image_paths = []
        
        for idx, prompt_data in enumerate(image_prompts, 1):
            output_path = os.path.join("output/images", f"scene_{idx:03d}.png")
            
            # Generate image with multiple attempts if needed
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Extract the prompt
                    base_prompt = prompt_data['prompt']
                    
                    # Generate the image
                    image, seed = self.generate_image(base_prompt)
                    
                    if image:
                        # Save in high quality
                        image.save(output_path, format="PNG", quality=100)
                        image_paths.append(output_path)
                        print(f"Generated image {idx}/{len(image_prompts)} with seed {seed}")
                        break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        print(f"Failed to generate image {idx} after {max_attempts} attempts: {str(e)}")
                    else:
                        print(f"Attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
        
        return image_paths 