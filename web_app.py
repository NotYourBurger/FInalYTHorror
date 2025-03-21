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

# HTML template
try:
    with open("web/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horror Story Generator</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>Horror Story Generator</h1>
        <p class="subtitle">Create cinematic horror videos with AI</p>
        
        <div id="status-container">
            <p id="status-message"></p>
        </div>
        
        <div id="progress-container" style="display:none;">
            <div class="progress-bar-container">
                <div id="progress-bar"></div>
            </div>
            <p id="progress-text">0%</p>
        </div>
        
        <div class="workflow">
            <div class="step" id="step1">
                <h2>1. Story Selection</h2>
                <div class="form-group">
                    <label>Select Subreddits:</label>
                    <div class="checkbox-group" id="subreddit-options">
                        <!-- Subreddit options will be populated here -->
                    </div>
                </div>
                <div class="form-group">
                    <label>Minimum Story Length:</label>
                    <input type="range" id="min-length" min="500" max="5000" step="500" value="1000">
                    <span id="min-length-value">1000</span> characters
                </div>
                <button id="fetch-stories">Fetch Stories</button>
                
                <div id="story-list-container" style="display:none;">
                    <h3>Select a Story:</h3>
                    <select id="story-list" size="5"></select>
                    <div id="story-preview"></div>
                    <button id="enhance-story" disabled>Enhance Story</button>
                </div>
            </div>
            
            <div class="step" id="step2" style="display:none;">
                <h2>2. Voice Narration</h2>
                <div class="form-group">
                    <label>Narrator Voice:</label>
                    <select id="voice-selection">
                        <option value="af_bella">Bella (Horror)</option>
                        <option value="en_joe">Joe (Male)</option>
                        <option value="en_emily">Emily (Female)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Narration Speed:</label>
                    <input type="range" id="voice-speed" min="0.5" max="1.2" step="0.05" value="0.85">
                    <span id="voice-speed-value">0.85</span>
                </div>
                <button id="generate-narration">Generate Narration</button>
                <div id="audio-player-container" style="display:none;">
                    <h3>Preview Narration:</h3>
                    <audio id="audio-player" controls></audio>
                </div>
            </div>
            
            <div class="step" id="step3" style="display:none;">
                <h2>3. Subtitles & Images</h2>
                <button id="generate-subtitles">Generate Subtitles</button>
                <div id="subtitles-preview" style="display:none;">
                    <h3>Subtitles Generated</h3>
                    <p>Subtitles have been created and will be used in the final video.</p>
                </div>
                
                <div id="image-generation" style="display:none;">
                    <h3>Generate Images</h3>
                    <div class="form-group">
                        <label>Visual Style:</label>
                        <select id="image-style">
                            <option value="Cinematic">Cinematic</option>
                            <option value="Realistic">Realistic</option>
                            <option value="Artistic">Artistic</option>
                        </select>
                    </div>
                    <button id="generate-images">Generate Images</button>
                    
                    <div id="image-grid-container" style="display:none;">
                        <h3>Generated Images:</h3>
                        <div id="image-grid"></div>
                    </div>
                </div>
            </div>
            
            <div class="step" id="step4" style="display:none;">
                <h2>4. Video Compilation</h2>
                <div class="form-group">
                    <label>Video Quality:</label>
                    <select id="video-quality">
                        <option value="6000k">High (6000k)</option>
                        <option value="4000k" selected>Medium (4000k)</option>
                        <option value="2000k">Low (2000k)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Special Effects:</label>
                    <div class="checkbox-item">
                        <input type="checkbox" id="dust-overlay" checked>
                        <label for="dust-overlay">Add dust overlay effect</label>
                    </div>
                </div>
                <button id="compile-video">Compile Video</button>
                
                <div id="video-container" style="display:none;">
                    <h3>Preview Video:</h3>
                    <video id="video-player" controls width="100%"></video>
                </div>
            </div>
            
            <div class="step" id="step5" style="display:none;">
                <h2>5. Export</h2>
                <div class="export-options">
                    <button onclick="exportFile('video')">Export Video</button>
                    <button onclick="exportFile('audio')">Export Audio</button>
                    <button onclick="exportFile('subtitles')">Export Subtitles</button>
                    <button onclick="exportFile('images')">Export Images</button>
                    <button onclick="exportProject()">Export Complete Project</button>
                </div>
                
                <div id="export-links"></div>
            </div>
        </div>
    </div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>""")
    print("✓ Created index.html template")
except Exception as e:
    print(f"Error creating index.html: {str(e)}")
    sys.exit(1)

# Create JavaScript file
try:
    with open("web/static/js/app.js", "w") as f:
        f.write("""// Global variables
let projectId = null;
let selectedStoryIndex = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    // Create a new project
    await createProject();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load subreddit options
    await loadSubreddits();
    
    // Set up range input displays
    document.getElementById('min-length').addEventListener('input', function() {
        document.getElementById('min-length-value').textContent = this.value;
    });
    
    document.getElementById('voice-speed').addEventListener('input', function() {
        document.getElementById('voice-speed-value').textContent = this.value;
    });
    
    showStatus('Ready to begin. Select subreddits and fetch stories.', 'info');
});

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
            showStatus('Failed to create project', 'error');
        }
    } catch (error) {
        showStatus('Error creating project: ' + error.message, 'error');
    }
}

function setupEventListeners() {
    // Story selection
    document.getElementById('fetch-stories').addEventListener('click', fetchStories);
    document.getElementById('story-list').addEventListener('change', previewStory);
    document.getElementById('enhance-story').addEventListener('click', enhanceStory);
    
    // Narration
    document.getElementById('generate-narration').addEventListener('click', generateNarration);
    
    // Subtitles and Images
    document.getElementById('generate-subtitles').addEventListener('click', generateSubtitles);
    document.getElementById('generate-images').addEventListener('click', generateImages);
    
    // Video
    document.getElementById('compile-video').addEventListener('click', compileVideo);
}

async function loadSubreddits() {
    try {
        const response = await fetch('/api/subreddits');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('subreddit-options');
            
            data.subreddits.forEach(subreddit => {
                const checkboxItem = document.createElement('div');
                checkboxItem.className = 'checkbox-item';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `subreddit-${subreddit}`;
                checkbox.value = subreddit;
                checkbox.checked = ['nosleep', 'shortscarystories'].includes(subreddit);
                
                const label = document.createElement('label');
                label.htmlFor = `subreddit-${subreddit}`;
                label.textContent = `r/${subreddit}`;
                
                checkboxItem.appendChild(checkbox);
                checkboxItem.appendChild(label);
                container.appendChild(checkboxItem);
            });
        } else {
            showStatus('Failed to load subreddits', 'error');
        }
    } catch (error) {
        showStatus('Error loading subreddits: ' + error.message, 'error');
    }
}

async function fetchStories() {
    showStatus('Fetching stories...', 'info');
    showProgress(true);
    
    // Get selected subreddits
    const checkboxes = document.querySelectorAll('#subreddit-options input:checked');
    const subreddits = Array.from(checkboxes).map(cb => cb.value);
    
    if (subreddits.length === 0) {
        showStatus('Please select at least one subreddit', 'error');
        showProgress(false);
        return;
    }
    
    // Get minimum length
    const minLength = document.getElementById('min-length').value;
    
    try {
        const response = await fetch(`/api/stories?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subreddits: subreddits,
                min_length: minLength
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Populate story list
            const storyList = document.getElementById('story-list');
            storyList.innerHTML = '';
            
            data.stories.forEach((story, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = story.title;
                storyList.appendChild(option);
            });
            
            // Show story list container
            document.getElementById('story-list-container').style.display = 'block';
            
            showStatus('Stories fetched successfully. Select a story to preview.', 'success');
        } else {
            showStatus('Failed to fetch stories: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error fetching stories: ' + error.message, 'error');
    }
    
    showProgress(false);
}

async function previewStory() {
    const storyList = document.getElementById('story-list');
    selectedStoryIndex = storyList.value;
    
    if (selectedStoryIndex === null) {
        return;
    }
    
    try {
        const response = await fetch(`/api/stories/${selectedStoryIndex}?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Show story preview
            const preview = document.getElementById('story-preview');
            preview.innerHTML = `
                <h4>${data.story.title}</h4>
                <p><strong>Author:</strong> ${data.story.author}</p>
                <p><strong>Subreddit:</strong> r/${data.story.subreddit}</p>
                <div class="story-content">${data.story.content.substring(0, 500)}...</div>
            `;
            
            // Enable enhance button
            document.getElementById('enhance-story').disabled = false;
        } else {
            showStatus('Failed to load story preview: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error loading story preview: ' + error.message, 'error');
    }
}

async function enhanceStory() {
    if (selectedStoryIndex === null) {
        showStatus('Please select a story first', 'error');
        return;
    }
    
    showStatus('Enhancing story...', 'info');
    showProgress(true);
    
    try {
        const response = await fetch(`/api/enhance?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                story_index: selectedStoryIndex
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show enhanced story
            const preview = document.getElementById('story-preview');
            preview.innerHTML += `
                <h4>Enhanced Version:</h4>
                <div class="story-content enhanced">${data.enhanced_story.substring(0, 500)}...</div>
            `;
            
            // Show next step
            document.getElementById('step2').style.display = 'block';
            
            showStatus('Story enhanced successfully', 'success');
        } else {
            showStatus('Failed to enhance story: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error enhancing story: ' + error.message, 'error');
    }
    
    showProgress(false);
}

async function generateNarration() {
    showStatus('Generating narration...', 'info');
    showProgress(true);
    
    const voice = document.getElementById('voice-selection').value;
    const speed = document.getElementById('voice-speed').value;
    
    try {
        const response = await fetch(`/api/narration?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voice: voice,
                speed: parseFloat(speed)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Start polling for status
            pollNarrationStatus();
        } else {
            showStatus('Failed to start narration: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error generating narration: ' + error.message, 'error');
        showProgress(false);
    }
}

async function pollNarrationStatus() {
    try {
        const response = await fetch(`/api/narration/status?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            updateProgress(data.progress);
            showStatus(data.message, 'info');
            
            if (data.status === 'completed') {
                // Show audio player
                const audioPlayer = document.getElementById('audio-player');
                audioPlayer.src = data.audio_url;
                document.getElementById('audio-player-container').style.display = 'block';
                
                // Show next step
                document.getElementById('step3').style.display = 'block';
                
                showStatus('Narration generated successfully', 'success');
                showProgress(false);
            } else if (data.status === 'error') {
                showStatus('Error generating narration: ' + data.message, 'error');
                showProgress(false);
            } else {
                // Continue polling
                setTimeout(pollNarrationStatus, 2000);
            }
        } else {
            showStatus('Failed to check narration status: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error checking narration status: ' + error.message, 'error');
        showProgress(false);
    }
}

async function generateSubtitles() {
    showStatus('Generating subtitles...', 'info');
    showProgress(true);
    
    try {
        const response = await fetch(`/api/subtitles?project_id=${projectId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Start polling for status
            pollSubtitlesStatus();
        } else {
            showStatus('Failed to start subtitle generation: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error generating subtitles: ' + error.message, 'error');
        showProgress(false);
    }
}

async function pollSubtitlesStatus() {
    try {
        const response = await fetch(`/api/subtitles/status?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            updateProgress(data.progress);
            showStatus(data.message, 'info');
            
            if (data.status === 'completed') {
                // Show subtitles preview
                document.getElementById('subtitles-preview').style.display = 'block';
                
                // Show image generation section
                document.getElementById('image-generation').style.display = 'block';
                
                showStatus('Subtitles generated successfully', 'success');
                showProgress(false);
            } else if (data.status === 'error') {
                showStatus('Error generating subtitles: ' + data.message, 'error');
                showProgress(false);
            } else {
                // Continue polling
                setTimeout(pollSubtitlesStatus, 2000);
            }
        } else {
            showStatus('Failed to check subtitles status: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error checking subtitles status: ' + error.message, 'error');
        showProgress(false);
    }
}

async function generateImages() {
    showStatus('Generating images...', 'info');
    showProgress(true);
    
    const style = document.getElementById('image-style').value;
    
    try {
        const response = await fetch(`/api/images?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                style: style
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Start polling for status
            pollImagesStatus();
        } else {
            showStatus('Failed to start image generation: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error generating images: ' + error.message, 'error');
        showProgress(false);
    }
}

async function pollImagesStatus() {
    try {
        const response = await fetch(`/api/images/status?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            updateProgress(data.progress);
            showStatus(data.message, 'info');
            
            if (data.status === 'completed') {
                // Show image grid
                const imageGrid = document.getElementById('image-grid');
                imageGrid.innerHTML = '';
                
                data.image_urls.forEach(url => {
                    const imgContainer = document.createElement('div');
                    imgContainer.className = 'image-container';
                    
                    const img = document.createElement('img');
                    img.src = url;
                    img.alt = 'Generated scene';
                    
                    imgContainer.appendChild(img);
                    imageGrid.appendChild(imgContainer);
                });
                
                document.getElementById('image-grid-container').style.display = 'block';
                
                // Show next step
                document.getElementById('step4').style.display = 'block';
                
                showStatus('Images generated successfully', 'success');
                showProgress(false);
            } else if (data.status === 'error') {
                showStatus('Error generating images: ' + data.message, 'error');
                showProgress(false);
            } else {
                // Continue polling
                setTimeout(pollImagesStatus, 2000);
            }
        } else {
            showStatus('Failed to check image generation status: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error checking image generation status: ' + error.message, 'error');
        showProgress(false);
    }
}

async function compileVideo() {
    showStatus('Compiling video...', 'info');
    showProgress(true);
    
    const quality = document.getElementById('video-quality').value;
    const useDustOverlay = document.getElementById('dust-overlay').checked;
    
    try {
        const response = await fetch(`/api/video?project_id=${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quality: quality,
                use_dust_overlay: useDustOverlay
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Start polling for status
            pollVideoStatus();
        } else {
            showStatus('Failed to start video compilation: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error compiling video: ' + error.message, 'error');
        showProgress(false);
    }
}

async function pollVideoStatus() {
    try {
        const response = await fetch(`/api/video/status?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            updateProgress(data.progress);
            showStatus(data.message, 'info');
            
            if (data.status === 'completed') {
                // Show video player
                const videoPlayer = document.getElementById('video-player');
                videoPlayer.src = data.video_url;
                document.getElementById('video-container').style.display = 'block';
                
                // Show next step
                document.getElementById('step5').style.display = 'block';
                
                showStatus('Video compiled successfully', 'success');
                showProgress(false);
            } else if (data.status === 'error') {
                showStatus('Error compiling video: ' + data.message, 'error');
                showProgress(false);
            } else {
                // Continue polling
                setTimeout(pollVideoStatus, 2000);
            }
        } else {
            showStatus('Failed to check video compilation status: ' + data.message, 'error');
            showProgress(false);
        }
    } catch (error) {
        showStatus('Error checking video compilation status: ' + error.message, 'error');
        showProgress(false);
    }
}

async function exportFile(type) {
    showStatus(`Preparing ${type} export...`, 'info');
    
    try {
        const response = await fetch(`/api/export/${type}?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Create download link
            const exportLinks = document.getElementById('export-links');
            
            const linkContainer = document.createElement('div');
            linkContainer.style.margin = '10px 0';
            
            const link = document.createElement('a');
            link.href = data.download_url;
            link.textContent = `Download ${type} file`;
            link.className = 'download-link';
            link.download = data.filename;
            
            linkContainer.appendChild(link);
            exportLinks.appendChild(linkContainer);
            
            showStatus(`${type} export ready for download`, 'success');
        } else {
            showStatus(`Failed to export ${type}: ${data.message}`, 'error');
        }
    } catch (error) {
        showStatus(`Error exporting ${type}: ${error.message}`, 'error');
    }
}

async function exportProject() {
    showStatus('Preparing project export...', 'info');
    showProgress(true);
    
    try {
        const response = await fetch(`/api/export/project?project_id=${projectId}`);
        const data = await response.json();
        
        if (data.success) {
            // Create download link
            const exportLinks = document.getElementById('export-links');
            
            const linkContainer = document.createElement('div');
            linkContainer.style.margin = '10px 0';
            
            const link = document.createElement('a');
            link.href = data.download_url;
            link.textContent = 'Download complete project';
            link.className = 'download-link';
            link.download = data.filename;
            
            linkContainer.appendChild(link);
            exportLinks.appendChild(linkContainer);
            
            showStatus('Project export ready for download', 'success');
        } else {
            showStatus('Failed to export project: ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('Error exporting project: ' + error.message, 'error');
    }
    
    showProgress(false);
}

function showStatus(message, type) {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = message;
    
    // Reset classes
    statusElement.className = '';
    
    // Add appropriate class
    if (type) {
        statusElement.classList.add(type);
    }
}

function showProgress(show, percent) {
    const progressContainer = document.getElementById('progress-container');
    
    if (show) {
        progressContainer.style.display = 'block';
        
        if (percent !== undefined) {
            updateProgress(percent);
        }
    } else {
        progressContainer.style.display = 'none';
    }
}

function updateProgress(percent) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}
""")
    print("✓ Created app.js file")
except Exception as e:
    print(f"Error creating app.js: {str(e)}")
    sys.exit(1)

# Create CSS file
try:
    with open("web/static/css/style.css", "w") as f:
        f.write("""/* Base styles */
body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
    margin: 0;
    padding: 0;
}

.container {
    width: 90%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    margin-bottom: 30px;
    color: #666;
}

/* Status messages */
#status-container {
    margin: 20px 0;
    padding: 10px;
    border-radius: 5px;
    background-color: #f8f8f8;
}

#status-message {
    margin: 0;
    padding: 5px;
}

#status-message.error {
    color: #d9534f;
    background-color: #f2dede;
    border-left: 4px solid #d9534f;
    padding-left: 10px;
}

#status-message.success {
    color: #5cb85c;
    background-color: #dff0d8;
    border-left: 4px solid #5cb85c;
    padding-left: 10px;
}

#status-message.info {
    color: #5bc0de;
    background-color: #d9edf7;
    border-left: 4px solid #5bc0de;
    padding-left: 10px;
}

/* Progress bar */
.progress-bar-container {
    width: 100%;
    height: 20px;
    background-color: #f0f0f0;
    border-radius: 10px;
    margin-bottom: 10px;
    overflow: hidden;
}

#progress-bar {
    height: 100%;
    background-color: #4CAF50;
    width: 0%;
    transition: width 0.3s ease;
}

#progress-text {
    text-align: center;
    margin: 0;
}

/* Workflow steps */
.workflow {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.step {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.step h2 {
    margin-top: 0;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

/* Form elements */
.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="range"] {
    width: 100%;
}

select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #45a049;
}

button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}

/* Checkbox groups */
.checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.checkbox-item {
    display: flex;
    align-items: center;
    margin-right: 15px;
}

.checkbox-item input {
    margin-right: 5px;
}

/* Story list and preview */
#story-list {
    width: 100%;
    margin-bottom: 15px;
}

#story-preview {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 15px;
    max-height: 300px;
    overflow-y: auto;
}

.story-content {
    white-space: pre-line;
    line-height: 1.5;
}

.story-content.enhanced {
    border-left: 3px solid #4CAF50;
    padding-left: 10px;
}

/* Audio player */
#audio-player {
    width: 100%;
    margin-top: 10px;
}

/* Image grid */
#image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.image-container {
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.image-container img {
    width: 100%;
    height: auto;
    display: block;
}

/* Export options */
.export-options {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
}

.download-link {
    display: inline-block;
    background-color: #2196F3;
    color: white;
    padding: 10px 15px;
    text-decoration: none;
    border-radius: 4px;
    margin-top: 5px;
}

.download-link:hover {
    background-color: #0b7dda;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        width: 95%;
    }
    
    .export-options {
        flex-direction: column;
    }
    
    #image-grid {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }
}
""")
    print("✓ Created style.css file")
except Exception as e:
    print(f"Error creating style.css: {str(e)}")
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