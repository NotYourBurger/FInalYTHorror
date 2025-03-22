# Import necessary modules
import os
import sys
import uuid
import threading
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Create Flask app with correct template folder
app = Flask(__name__, 
            template_folder=os.path.abspath("web/templates"),
            static_folder=os.path.abspath("web/static"))
CORS(app)  # Enable CORS for all routes

# Global variables to track generation status
generation_status = {
    'status': 'idle',
    'progress': 0,
    'message': '',
    'level': 'info',
    'images': [],
    'video': None
}

# Background thread for generation
generation_thread = None

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

# HTML template - Simple one-click interface
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

# Create JavaScript file
try:
    with open("web/static/js/app.js", "w") as f:
        f.write("""// Global variables
let isGenerating = false;
let socket = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('generate-btn').addEventListener('click', startGeneration);
    
    // Add initial log entry
    addLogEntry('System ready. Click "Generate Horror Video" to begin.', 'info');
});

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
        // Call the API to start the generation process
        const response = await fetch('/api/generate', {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to start generation');
        }
        
        // Start polling for updates
        startPolling();
        
    } catch (error) {
        addLogEntry('Error: ' + error.message, 'error');
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Horror Video';
        isGenerating = false;
    }
}

// Poll for updates
function startPolling() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update progress
            updateProgress(data.progress);
            
            // Update log if there's a new message
            if (data.message) {
                addLogEntry(data.message, data.level || 'info');
            }
            
            // Update images if available
            if (data.images && data.images.length > 0) {
                displayImages(data.images);
            }
            
            // Update video if available
            if (data.video) {
                displayVideo(data.video);
                
                // Complete
                addLogEntry('Horror video generation complete!', 'success');
                updateProgress(100);
                
                // Stop polling
                clearInterval(pollInterval);
                
                // Reset button
                document.getElementById('generate-btn').disabled = false;
                document.getElementById('generate-btn').textContent = 'Generate Horror Video';
                isGenerating = false;
            }
            
            // Check for completion or error
            if (data.status === 'error') {
                addLogEntry('Error: ' + data.message, 'error');
                clearInterval(pollInterval);
                document.getElementById('generate-btn').disabled = false;
                document.getElementById('generate-btn').textContent = 'Generate Horror Video';
                isGenerating = false;
            }
            
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
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
}

// Display the final video
function displayVideo(videoUrl) {
    const videoPlayer = document.getElementById('video-player');
    videoPlayer.src = videoUrl;
    
    const downloadLink = document.getElementById('download-link');
    downloadLink.href = videoUrl;
    downloadLink.download = 'horror_video.mp4';
    
    document.getElementById('video-container').style.display = 'block';
}

// Add a log entry to the terminal
function addLogEntry(message, type = 'info') {
    const terminal = document.getElementById('terminal-content');
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    
    terminal.appendChild(entry);
    
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

# Function to run the generation process
def run_generation():
    global generation_status
    
    try:
        # Update status
        generation_status['message'] = 'Initializing horror video generation...'
        generation_status['progress'] = 5
        
        # Try to import the prototype functions
        try:
            # Import the prototype.py module directly
            import prototype
            
            # Update status
            generation_status['message'] = 'Running complete horror video generation pipeline...'
            generation_status['progress'] = 10
            
            # Define a callback function to update progress
            def progress_callback(message, progress, level='info'):
                generation_status['message'] = message
                generation_status['progress'] = progress
                generation_status['level'] = level
                
                # If we have image paths, update the images list
                if 'image_paths' in generation_status and generation_status['image_paths']:
                    image_urls = [f'/output/images/{os.path.basename(img)}' for img in generation_status['image_paths']]
                    generation_status['images'] = image_urls
            
            # Run the complete pipeline from prototype.py
            results = prototype.run_complete_pipeline()
            
            if results:
                # Update status with results
                generation_status['status'] = 'completed'
                generation_status['progress'] = 100
                generation_status['message'] = 'Horror video generation complete!'
                generation_status['level'] = 'success'
                
                # Set image paths
                if 'image_paths' in results and results['image_paths']:
                    image_urls = [f'/output/images/{os.path.basename(img)}' for img in results['image_paths']]
                    generation_status['images'] = image_urls
                
                # Set video path
                if 'video_path' in results and results['video_path']:
                    generation_status['video'] = f'/output/videos/{os.path.basename(results["video_path"])}'
            else:
                # Update status with error
                generation_status['status'] = 'error'
                generation_status['message'] = 'Failed to generate horror video'
                generation_status['level'] = 'error'
                
        except ImportError as e:
            # Handle import error
            error_message = f"Error importing prototype.py: {str(e)}"
            print(error_message)
            
            # Suggest running setup.py
            error_message += "\n\nTry running setup.py first: python setup.py"
            
            generation_status['status'] = 'error'
            generation_status['message'] = error_message
            generation_status['level'] = 'error'
            
    except Exception as e:
        # Update status with error
        generation_status['status'] = 'error'
        generation_status['message'] = f'Error: {str(e)}'
        generation_status['level'] = 'error'
        print(f"Error in generation thread: {str(e)}")

# Routes
@app.route('/')
def index():
    try:
        return send_from_directory('web/templates', 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    global generation_thread, generation_status
    
    # Check if already generating
    if generation_status['status'] == 'running':
        return jsonify({'success': False, 'message': 'Generation already in progress'}), 400
    
    # Reset status
    generation_status = {
        'status': 'running',
        'progress': 0,
        'message': 'Starting generation process...',
        'level': 'info',
        'images': [],
        'video': None
    }
    
    # Start generation in background thread
    generation_thread = threading.Thread(target=run_generation)
    generation_thread.daemon = True
    generation_thread.start()
    
    return jsonify({'success': True, 'message': 'Generation started'})

@app.route('/api/status')
def status():
    return jsonify(generation_status)

@app.route('/output/<path:filename>')
def serve_output(filename):
    try:
        return send_from_directory('output', filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

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
            # Get ngrok configuration from setup
            try:
                from pyngrok import ngrok
                
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
            except Exception as e:
                print(f"Error setting up ngrok: {str(e)}")
                print("Running with local access only")
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            
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
        print("Try running setup.py first: python setup.py")
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