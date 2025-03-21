import os
import random
import numpy as np
from moviepy.editor import *
import traceback

class VideoService:
    """Service for video generation and processing"""
    
    def __init__(self):
        """Initialize video service"""
        # Create output directory
        os.makedirs("output/videos", exist_ok=True)
    
    def convert_timestamp_to_seconds(self, timestamp):
        """Convert SRT timestamp to seconds"""
        try:
            hours, minutes, seconds = timestamp.replace(',', '.').split(':')
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        except Exception as e:
            print(f"Error converting timestamp {timestamp}: {str(e)}")
            return 0.0
    
    def db_to_amplitude(self, db):
        """Convert decibels to amplitude ratio"""
        return 10 ** (db / 20)
    
    def create_video(self, image_prompts, image_paths, audio_path, title, srt_path=None, ambient_path=None, 
                    video_quality="4000k", cinematic_ratio=16/9, use_dust_overlay=True):
        """Create cinematic video with user-selected preferences"""
        try:
            print("Starting enhanced cinematic video creation...")
            
            # Create output directory if it doesn't exist
            output_dir = "output/videos"
            os.makedirs(output_dir, exist_ok=True)
            
            # Validate inputs
            if not image_paths or len(image_paths) == 0:
                raise ValueError("No image paths provided")
            
            if not os.path.exists(audio_path):
                raise ValueError(f"Audio file not found: {audio_path}")
            
            # Filter out non-existent image paths
            valid_image_paths = []
            valid_prompts = []
            for i, (prompt, path) in enumerate(zip(image_prompts, image_paths)):
                if os.path.exists(path):
                    valid_image_paths.append(path)
                    valid_prompts.append(prompt)
                else:
                    print(f"Warning: Image file not found: {path}")
            
            if not valid_image_paths:
                raise ValueError("No valid image files found")
            
            # Get audio duration
            try:
                audio = AudioFileClip(audio_path)
                total_duration = audio.duration
                print(f"Audio duration: {total_duration:.2f} seconds")
            except Exception as e:
                print(f"Error loading audio: {str(e)}")
                raise
            
            # Create clips from images with their specific timings and fill screen
            video_clips = []
            
            print(f"Processing {len(valid_image_paths)} images...")
            for i, (prompt_data, img_path) in enumerate(zip(valid_prompts, valid_image_paths)):
                try:
                    # Get timing from prompt data
                    start_time = self.convert_timestamp_to_seconds(prompt_data['timing'][0])
                    end_time = self.convert_timestamp_to_seconds(prompt_data['timing'][1])
                    duration = max(end_time - start_time, 1.0)  # Ensure minimum duration
                    
                    # Add random subtle tilt/rotation to image
                    tilt_angle = random.uniform(-2.0, 2.0)  # Random tilt between -2 and 2 degrees
                    zoom_factor = random.uniform(1.02, 1.08)  # Random zoom between 2-8%
                    
                    # Create clip with subtle zoom and rotation
                    img = ImageClip(img_path)
                    
                    # Ensure image fills the screen (16:9 aspect ratio)
                    target_width = 1920
                    target_height = 1080
                    
                    # Calculate dimensions to fill screen while maintaining aspect ratio
                    img_aspect = img.w / img.h
                    screen_aspect = target_width / target_height
                    
                    if img_aspect > screen_aspect:  # Image is wider than screen
                        new_height = target_height
                        new_width = int(new_height * img_aspect)
                    else:  # Image is taller than screen
                        new_width = target_width
                        new_height = int(new_width / img_aspect)
                    
                    # Resize to fill screen
                    img = img.resize(width=new_width, height=new_height)
                    
                    clip = (img
                       .set_duration(duration)
                       .set_start(start_time)
                       .resize(lambda t: zoom_factor + (0.1 * t/duration))  # Combine base zoom with gradual zoom
                       .rotate(lambda t: tilt_angle, expand=False)  # Apply subtle tilt
                       .set_position('center'))  # Ensure image is centered
                    
                    video_clips.append(clip)
                    print(f"Processed image {i+1}/{len(valid_image_paths)}")
                except Exception as e:
                    print(f"Error processing image {i+1}: {str(e)}")
                    # Continue with next image
            
            if not video_clips:
                raise ValueError("No video clips could be created from images")

            # Add transitions between clips
            final_clips = []
            for i, clip in enumerate(video_clips):
                try:
                    if i > 0:
                        # Add crossfade with previous clip
                        clip = clip.crossfadein(min(1.0, clip.duration/2))
                    final_clips.append(clip)
                except Exception as e:
                    print(f"Error adding transition to clip {i+1}: {str(e)}")
                    final_clips.append(clip)  # Add without transition

            # Combine all clips
            print("Combining video clips...")
            try:
                video = CompositeVideoClip(final_clips)
                # Resize to standard 16:9 resolution
                video = video.resize(width=1920, height=1080)
            except Exception as e:
                print(f"Error combining clips: {str(e)}")
                # Try a simpler approach if composite fails
                if len(final_clips) > 0:
                    video = concatenate_videoclips(final_clips, method="compose")
                    video = video.resize(width=1920, height=1080)
                else:
                    raise ValueError("No clips to combine")
            
            # Add subtitles if available
            subtitle_clip = None
            if srt_path and os.path.exists(srt_path):
                try:
                    print("Adding subtitles from: " + srt_path)
                    
                    # First try to use a better font for subtitles
                    subtitle_font = 'Arial-Bold'  # Default fallback
                    
                    # Try to find a better font on the system
                    try:
                        import matplotlib.font_manager as fm
                        fonts = fm.findSystemFonts()
                        for font in fonts:
                            if 'arial' in font.lower() and 'bold' in font.lower():
                                subtitle_font = font
                                break
                        print(f"Using font: {subtitle_font}")
                    except Exception as font_error:
                        print(f"Could not find system fonts: {str(font_error)}")
                    
                    # Create subtitle generator with improved settings
                    generator = lambda txt: TextClip(
                        txt,
                        font=subtitle_font,
                        fontsize=40,  # Larger size for better visibility
                        color='white',
                        stroke_color='black',
                        stroke_width=2,  # Thicker stroke for better visibility
                        method='caption',
                        size=(video.w * 0.8, None),  # Wider text area
                        align='center'
                    )
                    
                    # Create the subtitles clip
                    subtitle_clip = SubtitlesClip(srt_path, generator)
                    
                    # Set the position to bottom center with padding
                    subtitle_clip = subtitle_clip.set_position(('center', 0.85), relative=True)
                    
                    print("Subtitles added successfully")
                except Exception as e:
                    print(f"Error adding subtitles: {str(e)}")
                    traceback.print_exc()  # Print detailed error information
            
            # Create a list of clips to composite
            clips_to_composite = [video]
            
            # Add subtitle clip if available
            if subtitle_clip is not None:
                clips_to_composite.append(subtitle_clip)
            
            # Apply dust overlay if requested
            if use_dust_overlay:
                try:
                    # Create a simple dust overlay
                    dust_overlay_path = self.create_dust_overlay(1920, 1080, total_duration)
                    if dust_overlay_path and os.path.exists(dust_overlay_path):
                        dust_overlay = VideoFileClip(dust_overlay_path, audio=False)
                        clips_to_composite.append(dust_overlay.set_opacity(0.3).set_blend_mode("screen"))
                        print("Dust overlay applied successfully")
                except Exception as e:
                    print(f"Error applying dust overlay: {str(e)}")
            
            # Composite all clips together
            try:
                print(f"Compositing {len(clips_to_composite)} clips together...")
                video = CompositeVideoClip(clips_to_composite)
            except Exception as e:
                print(f"Error in final composition: {str(e)}")
            
            # Add ambient soundscape if available
            if ambient_path and os.path.exists(ambient_path):
                try:
                    print("Adding ambient sound design...")
                    ambient_audio = AudioFileClip(ambient_path)
                    
                    # Ensure ambient audio matches narration duration
                    if ambient_audio.duration < total_duration:
                        ambient_audio = afx.audio_loop(ambient_audio, duration=total_duration)
                    else:
                        ambient_audio = ambient_audio.subclip(0, total_duration)
                    
                    # Mix ambient sounds with narration (ambient at lower volume)
                    ambient_audio = ambient_audio.volumex(self.db_to_amplitude(-15))  # Lower volume for ambient
                    final_audio = CompositeAudioClip([audio, ambient_audio])
                except Exception as e:
                    print(f"Warning: Could not add ambient sound: {str(e)}")
                    final_audio = audio
            else:
                final_audio = audio

            # Set audio to video
            try:
                video = video.set_audio(final_audio)
            except Exception as e:
                print(f"Warning: Could not set audio: {str(e)}")
                # Try to continue without audio if it fails

            # Render final video
            print("Rendering final cinematic video...")
            output_file = os.path.join(output_dir, f"{title}.mp4")
            
            try:
                # Use selected video quality for rendering
                video.write_videofile(
                    output_file,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate=video_quality,
                    threads=4,
                    preset='medium',
                    ffmpeg_params=['-crf', '18']
                )
            except Exception as e:
                print(f"Warning: High quality render failed: {str(e)}")
                print("Trying with more compatible settings...")
                
                # Try with more compatible settings
                try:
                    video.write_videofile(
                        output_file,
                        fps=24,
                        codec='libx264',
                        audio_codec='aac',
                        bitrate='4000k',
                        threads=2,
                        preset='faster',
                        ffmpeg_params=['-crf', '23']
                    )
                except Exception as e2:
                    print(f"Error in video rendering: {str(e2)}")
                    # Try one last time with minimal settings
                    video.write_videofile(
                        output_file,
                        fps=24,
                        codec='libx264',
                        audio_codec='aac'
                    )

            # Cleanup
            try:
                video.close()
                audio.close()
                if subtitle_clip is not None:
                    subtitle_clip.close()
                
                print("Cinematic video creation completed successfully.")
                return output_file
            except Exception as e:
                print(f"Warning during cleanup: {str(e)}")
                return output_file if os.path.exists(output_file) else None

        except Exception as e:
            print(f"Error in video creation: {str(e)}")
            return None
    
    def create_dust_overlay(self, width, height, duration):
        """Create a simple dust overlay effect"""
        try:
            from PIL import Image, ImageDraw
            import tempfile
            
            # Create a temporary file for the overlay
            temp_dir = os.path.join("output", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            overlay_path = os.path.join(temp_dir, "dust_overlay.mp4")
            
            # Create multiple dust frames for animation
            num_frames = 24  # 1 second at 24fps
            frames = []
            
            for _ in range(num_frames):
                # Create a dust texture frame
                img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Add random dust particles
                for _ in range(1000):
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    size = random.randint(1, 3)
                    opacity = random.randint(50, 150)
                    draw.ellipse((x, y, x+size, y+size), fill=(255, 255, 255, opacity))
                
                frames.append(img)
            
            # Save frames as temporary images
            temp_frame_paths = []
            for i, frame in enumerate(frames):
                frame_path = os.path.join(temp_dir, f"dust_frame_{i:03d}.png")
                frame.save(frame_path)
                temp_frame_paths.append(frame_path)
            
            # Create a clip from the frames
            frame_clips = [ImageClip(frame_path).set_duration(1/24) for frame_path in temp_frame_paths]
            dust_clip = concatenate_videoclips(frame_clips, method="compose")
            dust_clip = dust_clip.loop(duration=duration)
            
            # Write the dust overlay video
            dust_clip.write_videofile(
                overlay_path,
                fps=24,
                codec='libx264',
                audio=False,
                preset='ultrafast'
            )
            
            # Clean up temporary frame files
            for frame_path in temp_frame_paths:
                try:
                    os.remove(frame_path)
                except:
                    pass
            
            return overlay_path
        except Exception as e:
            print(f"Could not create dust overlay: {str(e)}")
            return None 