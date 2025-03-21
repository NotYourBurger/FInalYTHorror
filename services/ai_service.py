from google import genai
import time

class AIService:
    """Service for AI-powered text generation and analysis"""
    
    def __init__(self, api_key):
        """Initialize the Gemini API client"""
        self.client = genai.Client(api_key=api_key)
        
    def select_best_story(self, stories, max_stories=10):
        """Select the best story from a list based on narrative potential"""
        # Take a subset of stories for selection
        selection_stories = stories[:min(max_stories, len(stories))]
        
        # Create a prompt for story selection
        post_titles = "\n".join([f"{i+1}. {post.title}" for i, post in enumerate(selection_stories)])

        selection_prompt = f"""Select ONE story number (1-{len(selection_stories)}) that has the strongest potential for a horror podcast narrative. Consider:
- Clear narrative structure
- Strong character development
- Unique premise
- Visual storytelling potential
- Atmospheric content

Available stories:
{post_titles}

Return only the number."""

        # Get story selection
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=selection_prompt
            ).text
            
            story_index = int(response.strip()) - 1
            return selection_stories[story_index]
        except (ValueError, IndexError) as e:
            # Return a random story if selection fails
            return random.choice(selection_stories)
    
    def enhance_story(self, story_text):
        """Enhance a story into a podcast format with intro/outro"""
        enhancement_prompt = """Transform this story into a voice over script with the following structure:

1. Start with a powerful hook about the story's theme (2-3 sentences)
2. Include this intro: "Welcome to The Withering Club, where we explore the darkest corners of human experience. I'm your host, Anna. Before we begin tonight's story, remember that the shadows you see might be watching back. Now, dim the lights and prepare yourself for tonight's tale..."
3. Tell the story with a clear beginning, middle, and end, focusing on:
   - Clear narrative flow
   - Building tension
   - Natural dialogue
   - Atmospheric descriptions
4. End with: "That concludes tonight's tale from The Withering Club. If this story kept you up at night, remember to like, share, and subscribe to join our growing community of darkness seekers. Until next time, remember... the best stories are the ones that follow you home. Sleep well, if you can."

Original Story: {content}

Return ONLY the complete script text with no additional formatting, explanations, or markdown."""

        # Get enhanced story
        enhanced_story = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=enhancement_prompt.format(content=story_text)
        ).text

        # Clean up the enhanced story
        enhanced_story = enhanced_story.strip()
        
        return enhanced_story
    
    def generate_scene_descriptions(self, subtitle_segments, delay_seconds=2):
        """Generate cinematic scene descriptions based on subtitle segments"""
        scene_descriptions = []
        
        chunk_size = 2
        max_retries = 3
        
        for i in range(0, len(subtitle_segments) - chunk_size + 1, chunk_size):
            chunk = subtitle_segments[i:i + chunk_size]
            combined_text = ' '.join([seg['text'] for seg in chunk])
            
            # Enhanced prompt focusing on visual storytelling and scenario creation
            prompt = f"""
            You are a horror film director. Create a vivid, cinematic scene description for this segment of narration.
            
            NARRATION: "{combined_text}"
            
            Imagine this as a specific moment in a horror film. Describe:
            1. The exact visual scenario that would be filmed (not abstract concepts)
            2. Characters' positions, expressions, and actions
            3. Setting details including lighting, weather, and environment
            4. Camera angle and framing (close-up, wide shot, etc.)
            5. Color palette and visual tone
            
            IMPORTANT:
            - Describe a SINGLE, SPECIFIC moment that could be photographed
            - Focus on what the VIEWER SEES, not what characters think or feel
            - Include specific visual details that create atmosphere
            - Avoid vague descriptions - be concrete and filmable
            - Write in present tense as if describing a film frame
            
            Example: "A woman stands in her dimly lit kitchen, gripping a bloodstained knife. Her face is illuminated only by moonlight streaming through venetian blinds, casting striped shadows across her vengeful expression. In the background, shadowy figures can be seen through a doorway, unaware of her presence. The camera frames her in a low-angle shot, emphasizing her newfound power."
            
            Return ONLY the scene description, no explanations or formatting.
            """
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    ).text
                    
                    # Clean up the response
                    cleaned_response = (response
                        .replace('**', '')
                        .replace('Scene:', '')
                        .replace('Description:', '')
                        .strip())
                    
                    scene_descriptions.append({
                        'start_time': chunk[0]['start_time'],
                        'end_time': chunk[-1]['end_time'],
                        'description': cleaned_response
                    })
                    
                    time.sleep(delay_seconds)
                    break
                    
                except Exception as e:
                    if "429" in str(e):  # Rate limit error
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * delay_seconds * 2
                            print(f"Rate limit hit, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"Failed after {max_retries} attempts, using fallback description")
                            fallback_desc = "A dimly lit room with shadows stretching across the walls. A figure stands motionless, their face obscured by darkness as moonlight filters through a nearby window."
                            scene_descriptions.append({
                                'start_time': chunk[0]['start_time'],
                                'end_time': chunk[-1]['end_time'],
                                'description': fallback_desc
                            })
                    else:
                        print(f"Error generating scene: {str(e)}")
                        break
        
        return scene_descriptions
    
    def generate_image_prompts(self, scene_descriptions, style="cinematic", delay_seconds=3):
        """Generate detailed Stable Diffusion prompts from scene descriptions"""
        # Style guidance for different visual approaches
        style_guidance = {
            "realistic": "photorealistic, intricate details, natural lighting, cinematic photography, 8k resolution, dramatic composition",
            "cinematic": "cinematic composition, dramatic lighting, film grain, anamorphic lens effect, professional cinematography, color grading, depth of field",
            "artistic": "digital art, stylized, vibrant colors, dramatic composition, concept art, trending on artstation, by Greg Rutkowski and Zdzisław Beksiński",
            "neutral": "balanced composition, masterful photography, perfect exposure, selective focus, attention-grabbing depth of field, highly atmospheric"
        }
        
        prompts = []
        style_desc = style_guidance.get(style, style_guidance["cinematic"])
        max_retries = 3
        
        for i, scene in enumerate(scene_descriptions):
            prompt_template = f"""
            You are a professional concept artist for horror films. Create a detailed image prompt for Stable Diffusion XL based on this scene description.
            
            SCENE DESCRIPTION: "{scene['description']}"
            
            Your task is to translate this scene into a precise, visual prompt that will generate a striking horror image.
            
            Follow these requirements:
            1. Start with the main subject and their action (e.g., "A pale woman clutching a bloodied photograph")
            2. Describe the exact setting with specific details (e.g., "in an abandoned Victorian nursery with peeling wallpaper")
            3. Specify lighting, atmosphere, and color palette (e.g., "lit only by a single candle, casting long shadows, desaturated blue tones")
            4. Include camera perspective and framing (e.g., "extreme close-up shot, shallow depth of field")
            5. Add these style elements: {style_desc}
            
            IMPORTANT:
            - Be extremely specific and visual - describe exactly what should appear in the image
            - Focus on a single, powerful moment that tells a story
            - Include precise details about expressions, positioning, and environment
            - Use strong visual language that creates mood and atmosphere
            - Keep the prompt under 400 characters but dense with visual information
            
            Return ONLY the prompt text with no explanations or formatting.
            """
            
            # Attempt to generate prompt with retries and delay
            for attempt in range(max_retries):
                try:
                    # Generate prompt using Gemini
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt_template
                    ).text
                    
                    # Enhance the prompt with standard terms
                    enhanced_prompt = f"{response.strip()}, highly detailed, cinematic lighting, atmospheric, 8k resolution"
                    
                    prompts.append({
                        'timing': (scene['start_time'], scene['end_time']),
                        'prompt': enhanced_prompt,
                        'original_description': scene['description']  # Store original for reference
                    })
                    
                    time.sleep(delay_seconds)  # Add delay between requests
                    break
                    
                except Exception as e:
                    if "429" in str(e):  # Resource exhausted error
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * delay_seconds * 2  # Exponential backoff
                            print(f"Rate limit hit, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"Failed after {max_retries} attempts, using fallback prompt")
                            # Use a fallback prompt based on scene description
                            fallback_prompt = f"Horror scene: {scene['description'][:100]}, dark atmosphere, cinematic lighting, film grain"
                            prompts.append({
                                'timing': (scene['start_time'], scene['end_time']),
                                'prompt': f"{fallback_prompt}, highly detailed, cinematic lighting, atmospheric, 8k resolution",
                                'original_description': scene['description']
                            })
                    else:
                        print(f"Error generating prompt {i+1}: {str(e)}")
                        break
        
        return prompts 