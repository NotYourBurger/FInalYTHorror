import os
import numpy as np
import soundfile as sf
import whisper
import datetime

class AudioService:
    """Service for audio generation and processing"""
    
    def __init__(self):
        """Initialize audio service"""
        # Create output directories
        os.makedirs("output/audio", exist_ok=True)
        os.makedirs("output/subtitles", exist_ok=True)
        
        # Initialize whisper model (lazy loading)
        self.whisper_model = None
    
    def generate_narration(self, script_text, voice="af_bella", speed=0.85):
        """Generate professional horror narration audio"""
        try:
            from kokoro import KPipeline
            
            # Initialize pipeline with horror-optimized settings
            pipeline = KPipeline(lang_code='a')
            
            # Generate audio with selected voice and speed
            generator = pipeline(
                script_text,
                voice=voice,
                speed=speed
            )
            
            # Generate and concatenate audio segments
            audio_data = np.concatenate([audio.numpy() for _, _, audio in generator])
            
            # Save high-quality audio file
            output_path = os.path.join("output/audio", "narration.wav")
            sf.write(output_path, audio_data, 24000)
            
            return output_path
        except ImportError:
            print("Kokoro TTS not available. Please install it first.")
            return None
    
    def generate_subtitles(self, audio_path):
        """Generate subtitles using Whisper model"""
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return None
        
        # Lazy load Whisper model
        if self.whisper_model is None:
            self.whisper_model = whisper.load_model("base")
        
        # Transcribe with timing info
        result = self.whisper_model.transcribe(
            audio_path,
            verbose=False,
            word_timestamps=True,
            fp16=False  # Set to True if GPU available
        )
        
        # Save SRT file
        srt_path = os.path.join("output/subtitles", "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            self.write_srt(result["segments"], srt_file)
        
        return srt_path
    
    def write_srt(self, segments, file):
        """Write SRT file from segments"""
        for i, segment in enumerate(segments, start=1):
            # Write segment number
            print(f"{i}", file=file)
            
            # Format timestamps (SRT format: HH:MM:SS,mmm)
            start = self.format_timestamp(segment["start"])
            end = self.format_timestamp(segment["end"])
            
            # Write timestamps
            print(f"{start} --> {end}", file=file)
            
            # Write text
            print(f"{segment['text'].strip()}", file=file)
            
            # Empty line between entries
            print("", file=file)
    
    def format_timestamp(self, seconds):
        """Format seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        milliseconds = int((seconds % 1) * 1000)
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def parse_srt_timestamps(self, srt_path):
        """Parse SRT file and extract timestamps with text"""
        if not os.path.exists(srt_path):
            print(f"SRT file not found: {srt_path}")
            return []
            
        segments = []
        current_segment = {}
        
        with open(srt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.isdigit():  # Segment number
                if current_segment:
                    segments.append(current_segment)
                    current_segment = {}
                
                i += 1
                # Parse timestamp line
                timestamp_line = lines[i].strip()
                start_time, end_time = timestamp_line.split(' --> ')
                
                i += 1
                # Get text (may be multiple lines)
                text = []
                while i < len(lines) and lines[i].strip():
                    text.append(lines[i].strip())
                    i += 1
                    
                current_segment = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': ' '.join(text)
                }
            i += 1
            
        if current_segment:
            segments.append(current_segment)
            
        return segments
    
    def generate_ambient_soundscape(self, scene_descriptions, audio_duration):
        """Generate ambient sound design based on scene descriptions"""
        # This is a placeholder for the ambient sound generation
        # In a real implementation, this would create a dynamic soundscape
        # based on the scene descriptions
        
        # For now, we'll just return a path to a dummy ambient sound file
        output_path = os.path.join("output/audio", "ambient_soundscape.wav")
        
        # Create a silent audio file as a placeholder
        sample_rate = 24000
        duration_samples = int(audio_duration * sample_rate)
        silent_audio = np.zeros(duration_samples)
        sf.write(output_path, silent_audio, sample_rate)
        
        return output_path 