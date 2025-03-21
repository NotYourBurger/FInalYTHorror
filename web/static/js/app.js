// Global variables
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
        // Step 1: Generate complete story (fetch, select, and enhance)
        addLogEntry('Fetching and enhancing horror story...', 'info');
        updateProgress(10);
        
        const storyResponse = await fetch(`/api/generate_story?project_id=${projectId}`, {
            method: 'POST'
        });
        
        const storyData = await storyResponse.json();
        
        if (!storyData.success) {
            throw new Error(storyData.message);
        }
        
        addLogEntry(`Story selected: "${storyData.title}"`, 'success');
        updateProgress(20);
        
        // Step 2: Generate narration
        addLogEntry('Generating voice narration...', 'info');
        updateProgress(30);
        
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
        await pollStatus('narration', 40);
        
        // Step 3: Generate subtitles
        addLogEntry('Generating subtitles and scene descriptions...', 'info');
        updateProgress(50);
        
        const subtitlesResponse = await fetch(`/api/subtitles?project_id=${projectId}`, {
            method: 'POST'
        });
        
        const subtitlesData = await subtitlesResponse.json();
        
        if (!subtitlesData.success) {
            throw new Error(subtitlesData.message);
        }
        
        // Poll for subtitles status
        await pollStatus('subtitles', 60);
        
        // Step 4: Generate images
        addLogEntry('Generating cinematic horror images...', 'info');
        updateProgress(70);
        
        const imagesResponse = await fetch(`/api/images?project_id=${projectId}`, {
            method: 'POST'
        });
        
        const imagesData = await imagesResponse.json();
        
        if (!imagesData.success) {
            throw new Error(imagesData.message);
        }
        
        // Poll for images status and display them
        const imageUrls = await pollImagesStatus(80);
        displayImages(imageUrls);
        
        // Step 5: Compile video
        addLogEntry('Compiling final horror video...', 'info');
        updateProgress(90);
        
        const videoResponse = await fetch(`/api/video?project_id=${projectId}`, {
            method: 'POST'
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