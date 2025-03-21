# Horror Story Generator

An AI-powered application that automatically creates cinematic horror videos by combining AI-generated narration, images, and audio.

![Horror Story Generator](assets/screenshots/app_screenshot.png)

## Features

- **Story Selection**: Fetch and enhance horror stories from Reddit
- **Voice Narration**: Generate professional-quality voice-overs with customizable voices and speeds
- **Subtitle Generation**: Create accurate subtitles with precise timestamps
- **Image Generation**: Generate cinematic horror images using Stable Diffusion XL
- **Video Compilation**: Combine all elements into a cinematic horror video with effects and transitions
- **Export Options**: Export videos, audio, and subtitles in various formats

## Installation

### Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended for image generation)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/horror-story-generator.git
   cd horror-story-generator
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create required directories:
   ```
   mkdir -p output/audio output/subtitles output/images output/videos data assets/icons
   ```

5. Set up API credentials:
   - Create a Reddit application at https://www.reddit.com/prefs/apps
   - Get a Google Gemini API key at https://ai.google.dev/
   - Update the credentials in `main.py` or create a `.env` file

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Start a new project from the home screen

3. Follow the workflow:
   - Select and enhance a horror story
   - Generate voice narration
   - Create subtitles
   - Generate images for key scenes
   - Compile the final video

4. Export your creation as a video file

## Project Structure 