# Import necessary modules
import os
import sys
import uuid
import threading
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import waitress

# Create Flask app with correct template folder
app = Flask(__name__, 
            template_folder=os.path.abspath("web/templates"),
            static_folder=os.path.abspath("web/static"))
CORS(app)  # Enable CORS for all routes

# Dictionary to store active projects
active_projects = {}

# Dictionary to store background tasks
background_tasks = {}

# Ensure all required directories exist
def ensure_directories():
    """Create all necessary directories for the application."""
    directories = [
        "web/templates",
        "web/static/js",
        "web/static/css",
        "output",
        "output/audio",
        "output/images",
        "output/videos",
        "output/subtitles",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory created/verified: {directory}")

# Call the function to ensure directories exist
ensure_directories()

# Create a simplified HTML template
try:
    with open("web/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horror Story Video Generator</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>Horror Story Video Generator</h1>
        <p class="subtitle">Create cinematic horror videos with AI in one click</p>
        
        <div class="main-controls">
            <button id="generate-btn" class="primary-btn">Generate Horror Video</button>
        </div>
        
        <div id="status-container">
            <h2>Status</h2>
            <div id="terminal">
                <div id="terminal-content"></div>
            </div>
        </div>
        
        <div id="progress-container">
            <div class="progress-bar-container">
                <div id="progress-bar"></div>
            </div>
            <p id="progress-text">0%</p>
        </div>
        
        <div id="image-preview" style="display:none;">
            <h2>Generated Images</h2>
            <div id="image-grid"></div>
        </div>
        
        <div id="video-container" style="display:none;">
            <h2>Your Horror Video</h2>
            <video id="video-player" controls width="100%"></video>
            <div class="download-container">
                <a id="download-link" class="download-btn">Download Video</a>
            </div>
        </div>
    </div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>""")
    print("✓ Created simplified index.html template")
except Exception as e:
    print(f"Error creating index.html: {str(e)}")
    sys.exit(1)

# Create CSS file with simplified styling
try:
    with open("web/static/css/style.css", "w") as f:
        f.write("""/* Base styles */
body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #f0f0f0;
    background-color: #121212;
    margin: 0;
    padding: 0;
}

.container {
    width: 90%;
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

h1, h2 {
    text-align: center;
    margin-bottom: 10px;
    color: #e91e63;
}

.subtitle {
    text-align: center;
    margin-bottom: 30px;
    color: #aaa;
}

/* Main controls */
.main-controls {
    text-align: center;
    margin: 30px 0;
}

.primary-btn {
    background-color: #e91e63;
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 30px;
    cursor: pointer;
    font-size: 18px;
    font-weight: bold;
    box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);
    transition: all 0.3s;
}

.primary-btn:hover {
    background-color: #d81b60;
    box-shadow: 0 6px 12px rgba(233, 30, 99, 0.4);
    transform: translateY(-2px);
}

.primary-btn:disabled {
    background-color: #555;
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
}

/* Terminal */
#terminal {
    background-color: #1e1e1e;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
    height: 200px;
    overflow-y: auto;
    font-family: monospace;
    border: 1px solid #333;
}

#terminal-content {
    color: #0f0;
}

.log-entry {
    margin: 5px 0;
    line-height: 1.4;
}

.log-error {
    color: #ff5252;
}

.log-success {
    color: #4caf50;
}

.log-info {
    color: #2196f3;
}

/* Progress bar */
.progress-bar-container {
    width: 100%;
    height: 20px;
    background-color: #333;
    border-radius: 10px;
    margin: 20px 0;
    overflow: hidden;
}

#progress-bar {
    height: 100%;
    background-color: #e91e63;
    width: 0%;
    transition: width 0.3s ease;
}

#progress-text {
    text-align: center;
    margin: 0;
    color: #aaa;
}

/* Image grid */
#image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.image-container {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    transition: transform 0.3s;
}

.image-container:hover {
    transform: scale(1.05);
}

.image-container img {
    width: 100%;
    height: auto;
    display: block;
}

/* Video container */
#video-container {
    margin: 30px 0;
    background-color: #1e1e1e;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

#video-player {
    width: 100%;
    border-radius: 4px;
    margin-bottom: 15px;
}

.download-container {
    text-align: center;
    margin-top: 15px;
}

.download-btn {
    display: inline-block;
    background-color: #4caf50;
    color: white;
    padding: 10px 20px;
    text-decoration: none;
    border-radius: 30px;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    cursor: pointer;
    transition: all 0.3s;
}

.download-btn:hover {
    background-color: #43a047;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        width: 95%;
    }
    
    #image-grid {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }
}
""")
    print("✓ Created simplified style.css file")
except Exception as e:
    print(f"Error creating style.css: {str(e)}")
    sys.exit(1)

# Create JavaScript file for one-click process
try:
    with open("web/static/js/app.js", "w") as f:
        f.write("""// Global variables
let projectId = null;
let isGenerating = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('generate-btn').addEventListener('click', startGeneration);
    
    // Create a new project on load
    createProject();
    
    // Add initial log entry
    addLogEntry('System ready. Click "Generate Horror Video" to begin.', 'info');
});

// Create a new project
async function createProject() {
    try {
        const response = await fetch('/api/projects', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            projectId = data.project_id;
            console.log('Project created with ID:', projectId);
        } else {
            addLogEntry('Failed to create project: ' + data.message, 'error');
        }
    } catch (error) {
        addLogEntry('Error creating project: ' + error.message, 'error');
    }
}

// Start the generation process
async function startGeneration() {
    if (isGenerating) return;
    
    isGenerating = true;
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    // Reset UI
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('video-container').style.display = 'none';
    document.getElementById('image-grid').innerHTML = '';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
    document.getElementById('terminal-content').innerHTML = '';
    
    addLogEntry('Starting horror video generation process...', 'info');
    
    try {
        // Step 1: Fetch stories
        addLogEntry('Fetching horror stories from Reddit...', 'info');
        updateProgress(5);
        
        const fetchResponse = await fetch(`/api/stories?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subreddits: ['nosleep', 'shortscarystories', 'creepypasta'],
                min_length: 1500
            })
        });
        
        const fetchData = await fetchResponse.json();
        
        if (!fetchData.success) {
            throw new Error(fetchData.message);
        }
        
        addLogEntry(`Found ${fetchData.stories.length} horror stories.`, 'success');
        
        // Step 2: Select and enhance a story
        addLogEntry('Selecting the best story and enhancing it...', 'info');
        updateProgress(15);
        
        // Select the first story (in a real app, you might want to use a better selection algorithm)
        const storyIndex = 0;
        
        const enhanceResponse = await fetch(`/api/enhance?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                story_index: storyIndex
            })
        });
        
        const enhanceData = await enhanceResponse.json();
        
        if (!enhanceData.success) {
            throw new Error(enhanceData.message);
        }
        
        addLogEntry('Story enhanced successfully.', 'success');
        
        // Step 3: Generate narration
        addLogEntry('Generating voice narration...', 'info');
        updateProgress(25);
        
        const narrationResponse = await fetch(`/api/narration?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voice: 'af_bella',
                speed: 0.85
            })
        });
        
        const narrationData = await narrationResponse.json();
        
        if (!narrationData.success) {
            throw new Error(narrationData.message);
        }
        
        // Poll for narration status
        await pollStatus('narration', 35);
        
        // Step 4: Generate subtitles
        addLogEntry('Generating subtitles...', 'info');
        updateProgress(45);
        
        const subtitlesResponse = await fetch(`/api/subtitles?project_id=${projectId}`, {
            method: 'POST'
        });
        
        const subtitlesData = await subtitlesResponse.json();
        
        if (!subtitlesData.success) {
            throw new Error(subtitlesData.message);
        }
        
        // Poll for subtitles status
        await pollStatus('subtitles', 55);
        
        // Step 5: Generate images
        addLogEntry('Generating cinematic horror images...', 'info');
        updateProgress(65);
        
        const imagesResponse = await fetch(`/api/images?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                style: 'Cinematic'
            })
        });
        
        const imagesData = await imagesResponse.json();
        
        if (!imagesData.success) {
            throw new Error(imagesData.message);
        }
        
        // Poll for images status and display them
        const imageUrls = await pollImagesStatus(75);
        displayImages(imageUrls);
        
        // Step 6: Compile video
        addLogEntry('Compiling final horror video...', 'info');
        updateProgress(85);
        
        const videoResponse = await fetch(`/api/video?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quality: '4000k',
                use_dust_overlay: true
            })
        });
        
        const videoData = await videoResponse.json();
        
        if (!videoData.success) {
            throw new Error(videoData.message);
        }
        
        // Poll for video status and display it
        const videoUrl = await pollVideoStatus(95);
        displayVideo(videoUrl);
        
        // Complete
        addLogEntry('Horror video generation complete!', 'success');
        updateProgress(100);
        
    } catch (error) {
        addLogEntry('Error generating video: ' + error.message, 'error');
        updateProgress(0);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Horror Video';
        isGenerating = false;
    }
}

// Poll for status of a task
async function pollStatus(task, progressStart) {
    return new Promise((resolve, reject) => {
        const maxAttempts = 60; // 5 minutes max (5s intervals)
        let attempts = 0;
        
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/${task}/status?project_id=${projectId}`);
                const data = await response.json();
                
                if (!data.success) {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                // Update progress
                const taskProgress = data.progress || 0;
                updateProgress(progressStart + (taskProgress * 0.1)); // 10% of the total progress
                
                // Update log
                if (data.message) {
                    addLogEntry(data.message, 'info', false);
                }
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    resolve(data);
                    return;
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    reject(new Error(`${task} process timed out`));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        };
        
        const interval = setInterval(checkStatus, 5000);
        checkStatus(); // Check immediately
    });
}

// Poll for images status and return image URLs
async function pollImagesStatus(progressStart) {
    return new Promise((resolve, reject) => {
        const maxAttempts = 60;
        let attempts = 0;
        
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/images/status?project_id=${projectId}`);
                const data = await response.json();
                
                if (!data.success) {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                // Update progress
                const taskProgress = data.progress || 0;
                updateProgress(progressStart + (taskProgress * 0.1));
                
                // Update log
                if (data.message) {
                    addLogEntry(data.message, 'info', false);
                }
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    resolve(data.image_urls);
                    return;
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    reject(new Error('Image generation timed out'));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        };
        
        const interval = setInterval(checkStatus, 5000);
        checkStatus(); // Check immediately
    });
}

// Poll for video status and return video URL
async function pollVideoStatus(progressStart) {
    return new Promise((resolve, reject) => {
        const maxAttempts = 60;
        let attempts = 0;
        
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/video/status?project_id=${projectId}`);
                const data = await response.json();
                
                if (!data.success) {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                // Update progress
                const taskProgress = data.progress || 0;
                updateProgress(progressStart + (taskProgress * 0.05));
                
                // Update log
                if (data.message) {
                    addLogEntry(data.message, 'info', false);
                }
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    resolve(data.video_url);
                    return;
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    reject(new Error(data.message));
                    return;
                }
                
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    reject(new Error('Video compilation timed out'));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        };
        
        const interval = setInterval(checkStatus, 5000);
        checkStatus(); // Check immediately
    });
}

// Display images in the grid
function displayImages(imageUrls) {
    const imageGrid = document.getElementById('image-grid');
    imageGrid.innerHTML = '';
    
    imageUrls.forEach(url => {
        const imgContainer = document.createElement('div');
        imgContainer.className = 'image-container';
        
        const img = document.createElement('img');
        img.src = url;
        img.alt = 'Generated horror scene';
        img.loading = 'lazy';
        
        imgContainer.appendChild(img);
        imageGrid.appendChild(imgContainer);
    });
    
    document.getElementById('image-preview').style.display = 'block';
    
    // Scroll to images
    document.getElementById('image-preview').scrollIntoView({ behavior: 'smooth' });
}

// Display the final video
function displayVideo(videoUrl) {
    const videoPlayer = document.getElementById('video-player');
    videoPlayer.src = videoUrl;
    
    const downloadLink = document.getElementById('download-link');
    downloadLink.href = videoUrl;
    downloadLink.download = 'horror_video.mp4';
    
    document.getElementById('video-container').style.display = 'block';
    
    // Scroll to video
    document.getElementById('video-container').scrollIntoView({ behavior: 'smooth' });
}

// Add a log entry to the terminal
function addLogEntry(message, type = 'info', newLine = true) {
    const terminal = document.getElementById('terminal-content');
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    
    if (newLine || terminal.children.length === 0) {
        terminal.appendChild(entry);
    } else {
        // Replace the last entry
        terminal.replaceChild(entry, terminal.lastChild);
    }
    
    // Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
}

// Update the progress bar
function updateProgress(percent) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    percent = Math.min(100, Math.max(0, percent)); // Clamp between 0-100
    
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
}
""")
    print("✓ Created simplified app.js file")
except Exception as e:
    print(f"Error creating app.js: {str(e)}")
    sys.exit(1)

# Mock services for demonstration
# In a real application, you would import these from your actual modules
class MockRedditService:
    def get_subreddit_list(self):
        return ["nosleep", "shortscarystories", "creepypasta", "letsnotmeet", "libraryofshadows"]
    
    def fetch_stories(self, subreddits, min_length):
        # Mock implementation
        return []
    
    def mark_story_used(self, story_id):
        pass

class MockAIService:
    def enhance_story(self, content):
        return content
    
    def generate_scene_descriptions(self, subtitle_segments):
        return []
    
    def generate_image_prompts(self, scene_descriptions, style):
        return []

class MockAudioService:
    def generate_narration(self, text, voice, speed):
        return "output/audio/narration.mp3"
    
    def generate_subtitles(self, audio_path):
        return "output/subtitles/subtitles.srt"
    
    def parse_srt_timestamps(self, srt_path):
        return []

class MockImageService:
    def generate_story_images(self, prompts):
        return ["output/images/image1.jpg", "output/images/image2.jpg"]

class MockVideoService:
    def create_video(self, prompts, image_paths, audio_path, title, srt_path, video_quality, use_dust_overlay):
        return "output/videos/video.mp4"

# Initialize mock services
# In a real application, replace these with your actual service instances
reddit_service = MockRedditService()
ai_service = MockAIService()
audio_service = MockAudioService()
image_service = MockImageService()
video_service = MockVideoService()

# API routes
@app.route('/')
def index():
    try:
        return send_from_directory('web/templates', 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        project_id = str(uuid.uuid4())
        active_projects[project_id] = {
            'story_data': None,
            'audio_path': None,
            'subtitles_path': None,
            'scene_descriptions': None,
            'image_prompts': None,
            'image_paths': None,
            'video_path': None,
            'stories': []
        }
        return jsonify({'success': True, 'project_id': project_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/subreddits')
def get_subreddits():
    subreddits = reddit_service.get_subreddit_list()
    return jsonify({'success': True, 'subreddits': subreddits})

@app.route('/api/stories', methods=['POST'])
def fetch_stories():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    data = request.json
    subreddits = data.get('subreddits', [])
    min_length = int(data.get('min_length', 1000))
    
    try:
        stories = reddit_service.fetch_stories(subreddits=subreddits, min_length=min_length)
        
        # Convert to serializable format
        story_data = []
        for story in stories:
            story_data.append({
                'id': story.id,
                'title': story.title,
                'author': story.author.name,
                'subreddit': story.subreddit.display_name,
                'content': story.selftext,
                'url': story.url
            })
        
        active_projects[project_id]['stories'] = story_data
        
        return jsonify({
            'success': True, 
            'stories': story_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/enhance', methods=['POST'])
def enhance_story():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    data = request.json
    story_index = int(data.get('story_index', 0))
    
    try:
        stories = active_projects[project_id]['stories']
        if story_index < 0 or story_index >= len(stories):
            return jsonify({'success': False, 'message': 'Invalid story index'})
        
        story = stories[story_index]
        
        # Enhance the story
        enhanced_story = ai_service.enhance_story(story['content'])
        
        # Update project data
        active_projects[project_id]['story_data'] = {
            'title': story['title'],
            'original': story['content'],
            'enhanced': enhanced_story,
            'subreddit': story['subreddit'],
            'story_id': story['id']
        }
        
        # Mark story as used
        reddit_service.mark_story_used(story['id'])
        
        return jsonify({'success': True, 'enhanced_story': enhanced_story})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def narration_worker(project_id, voice, speed):
    try:
        project = active_projects[project_id]
        if not project['story_data']:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'No story data available'
            return
        
        # Generate narration
        background_tasks[project_id]['status'] = 'processing'
        background_tasks[project_id]['progress'] = 10
        background_tasks[project_id]['message'] = 'Generating narration...'
        
        audio_path = audio_service.generate_narration(
            project['story_data']['enhanced'],
            voice=voice,
            speed=speed
        )
        
        if audio_path:
            project['audio_path'] = audio_path
            background_tasks[project_id]['status'] = 'completed'
            background_tasks[project_id]['progress'] = 100
            background_tasks[project_id]['message'] = 'Narration generated successfully'
        else:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'Failed to generate narration'
    except Exception as e:
        background_tasks[project_id]['status'] = 'error'
        background_tasks[project_id]['message'] = str(e)

@app.route('/api/narration', methods=['POST'])
def generate_narration():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    data = request.json
    voice = data.get('voice', 'af_bella')
    speed = float(data.get('speed', 0.85))
    
    # Start background task
    background_tasks[project_id] = {
        'task': 'narration',
        'status': 'starting',
        'progress': 0,
        'message': 'Starting narration generation...'
    }
    
    thread = threading.Thread(
        target=narration_worker,
        args=(project_id, voice, speed)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Narration generation started',
        'task_id': project_id
    })

@app.route('/api/narration/status')
def narration_status():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in background_tasks:
        return jsonify({'success': False, 'message': 'Invalid task ID'})
    
    task = background_tasks[project_id]
    
    if task['status'] == 'completed':
        # Get audio URL
        audio_path = active_projects[project_id]['audio_path']
        audio_url = f'/output/audio/{os.path.basename(audio_path)}'
        
        return jsonify({
            'success': True,
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message'],
            'audio_url': audio_url
        })
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    })

def subtitles_worker(project_id):
    try:
        project = active_projects[project_id]
        if not project['audio_path']:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'No audio file available'
            return
        
        # Generate subtitles
        background_tasks[project_id]['status'] = 'processing'
        background_tasks[project_id]['progress'] = 10
        background_tasks[project_id]['message'] = 'Generating subtitles...'
        
        srt_path = audio_service.generate_subtitles(project['audio_path'])
        
        if srt_path:
            project['subtitles_path'] = srt_path
            
            # Parse subtitles for scene descriptions
            background_tasks[project_id]['progress'] = 50
            background_tasks[project_id]['message'] = 'Parsing subtitles...'
            
            subtitle_segments = audio_service.parse_srt_timestamps(srt_path)
            
            # Generate scene descriptions
            background_tasks[project_id]['progress'] = 70
            background_tasks[project_id]['message'] = 'Generating scene descriptions...'
            
            scene_descriptions = ai_service.generate_scene_descriptions(subtitle_segments)
            project['scene_descriptions'] = scene_descriptions
            
            background_tasks[project_id]['status'] = 'completed'
            background_tasks[project_id]['progress'] = 100
            background_tasks[project_id]['message'] = 'Subtitles and scene descriptions generated'
        else:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'Failed to generate subtitles'
    except Exception as e:
        background_tasks[project_id]['status'] = 'error'
        background_tasks[project_id]['message'] = str(e)

@app.route('/api/subtitles', methods=['POST'])
def generate_subtitles():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    # Start background task
    background_tasks[project_id] = {
        'task': 'subtitles',
        'status': 'starting',
        'progress': 0,
        'message': 'Starting subtitle generation...'
    }
    
    thread = threading.Thread(
        target=subtitles_worker,
        args=(project_id,)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Subtitle generation started',
        'task_id': project_id
    })

@app.route('/api/subtitles/status')
def subtitles_status():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in background_tasks:
        return jsonify({'success': False, 'message': 'Invalid task ID'})
    
    task = background_tasks[project_id]
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    })

def images_worker(project_id, style):
    try:
        project = active_projects[project_id]
        if not project['scene_descriptions']:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'No scene descriptions available'
            return
        
        # Generate image prompts
        background_tasks[project_id]['status'] = 'processing'
        background_tasks[project_id]['progress'] = 10
        background_tasks[project_id]['message'] = 'Generating image prompts...'
        
        image_prompts = ai_service.generate_image_prompts(
            project['scene_descriptions'], 
            style=style.lower()
        )
        project['image_prompts'] = image_prompts
        
        # Generate images
        background_tasks[project_id]['progress'] = 30
        background_tasks[project_id]['message'] = 'Generating images...'
        
        image_paths = image_service.generate_story_images(image_prompts)
        
        if image_paths:
            project['image_paths'] = image_paths
            background_tasks[project_id]['status'] = 'completed'
            background_tasks[project_id]['progress'] = 100
            background_tasks[project_id]['message'] = 'Images generated successfully'
        else:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'Failed to generate images'
    except Exception as e:
        background_tasks[project_id]['status'] = 'error'
        background_tasks[project_id]['message'] = str(e)

@app.route('/api/images', methods=['POST'])
def generate_images():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    data = request.json
    style = data.get('style', 'Cinematic')
    
    # Start background task
    background_tasks[project_id] = {
        'task': 'images',
        'status': 'starting',
        'progress': 0,
        'message': 'Starting image generation...'
    }
    
    thread = threading.Thread(
        target=images_worker,
        args=(project_id, style)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Image generation started',
        'task_id': project_id
    })

@app.route('/api/images/status')
def images_status():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in background_tasks:
        return jsonify({'success': False, 'message': 'Invalid task ID'})
    
    task = background_tasks[project_id]
    
    if task['status'] == 'completed':
        # Get image URLs
        image_paths = active_projects[project_id]['image_paths']
        image_urls = [f'/output/images/{os.path.basename(path)}' for path in image_paths]
        
        return jsonify({
            'success': True,
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message'],
            'image_urls': image_urls
        })
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    })

def video_worker(project_id, quality, use_dust_overlay):
    try:
        project = active_projects[project_id]
        if not project['image_paths'] or not project['audio_path']:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'Missing required files'
            return
        
        # Compile video
        background_tasks[project_id]['status'] = 'processing'
        background_tasks[project_id]['progress'] = 10
        background_tasks[project_id]['message'] = 'Compiling video...'
        
        video_path = video_service.create_video(
            project['image_prompts'],
            project['image_paths'],
            project['audio_path'],
            project['story_data']['title'],
            srt_path=project['subtitles_path'],
            video_quality=quality,
            use_dust_overlay=use_dust_overlay
        )
        
        if video_path:
            project['video_path'] = video_path
            background_tasks[project_id]['status'] = 'completed'
            background_tasks[project_id]['progress'] = 100
            background_tasks[project_id]['message'] = 'Video compiled successfully'
        else:
            background_tasks[project_id]['status'] = 'error'
            background_tasks[project_id]['message'] = 'Failed to compile video'
    except Exception as e:
        background_tasks[project_id]['status'] = 'error'
        background_tasks[project_id]['message'] = str(e)

@app.route('/api/video', methods=['POST'])
def compile_video():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in active_projects:
        return jsonify({'success': False, 'message': 'Invalid project ID'})
    
    data = request.json
    quality = data.get('quality', '4000k')
    use_dust_overlay = data.get('use_dust_overlay', True)
    
    # Start background task
    background_tasks[project_id] = {
        'task': 'video',
        'status': 'starting',
        'progress': 0,
        'message': 'Starting video compilation...'
    }
    
    thread = threading.Thread(
        target=video_worker,
        args=(project_id, quality, use_dust_overlay)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Video compilation started',
        'task_id': project_id
    })

@app.route('/api/video/status')
def video_status():
    project_id = request.args.get('project_id')
    if not project_id or project_id not in background_tasks:
        return jsonify({'success': False, 'message': 'Invalid task ID'})
    
    task = background_tasks[project_id]
    
    if task['status'] == 'completed':
        # Get video URL
        video_path = active_projects[project_id]['video_path']
        video_url = f'/output/videos/{os.path.basename(video_path)}'
        
        return jsonify({
            'success': True,
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message'],
            'video_url': video_url
        })
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    })

# Serve output files
@app.route('/output/<path:filename>')
def serve_output(filename):
    try:
        return send_from_directory('output', filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('web/static', path)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Main function to run the app
def main():
    try:
        # Check if running in Google Colab
        try:
            import google.colab
            IN_COLAB = True
        except ImportError:
            IN_COLAB = False
            
        if IN_COLAB:
            print("\n🔄 Setting up Google Colab for external access...")
            
            # Install flask-ngrok if not already installed
            import subprocess
            subprocess.run(["pip", "install", "pyngrok"], check=True)
            
            # Import and configure ngrok directly
            from pyngrok import ngrok
            import os
            
            # Set ngrok auth token
            ngrok_auth_token = "2kjfVhuL1QZI4wwCIOOAe6pgunk_7dCPcQqfiBkjLzFduLRQU"
            ngrok.set_auth_token(ngrok_auth_token)
            
            # Start ngrok tunnel
            port = 5000
            public_url = ngrok.connect(port).public_url
            
            print("\n" + "="*50)
            print(f"✅ NGROK PUBLIC URL: {public_url}")
            print(f"📱 You can access this URL from your phone or any device")
            print("="*50 + "\n")
            
            # Run Flask app
            print("\n⚙️ Starting web server...")
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            
        else:
            # Not in Colab, try to get local IP for LAN access
            print("\n🔍 Finding your local IP address...")
            
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            print(f"\n📡 Your app will be available at:")
            print(f"🖥️ Local URL: http://127.0.0.1:5000")
            print(f"📱 LAN URL: http://{local_ip}:5000 (accessible from devices on your network)")
            print("\n⚠️ Note: To access from your phone, both devices must be on the same network")
            
            # Run Flask with host='0.0.0.0' to make it accessible on the network
            app.run(host='0.0.0.0', port=5000, debug=True)
            
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")
        print("Try installing the required packages: pip install flask flask-cors flask-ngrok")
        sys.exit(1)

if __name__ == "__main__":
    try:
        print("Starting Horror Story Generator Web App...")
        main()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
        sys.exit(1) 