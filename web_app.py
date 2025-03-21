# Continue from previous code...

# HTML template
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

# API routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/projects', methods=['POST'])
def create_project():
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
    return send_from_directory('output', filename)

# Main function to run the app
def main():
    # Create ngrok tunnel
    try:
        # Try to use ngrok for public URL
        from pyngrok import ngrok
        
        # Set up ngrok
        port = 5000
        public_url = ngrok.connect(port).public_url
        print(f" * Running on {public_url}")
        print(f" * Local URL: http://127.0.0.1:{port}")
        
        # Run with waitress
        waitress.serve(app, host='0.0.0.0', port=port)
    except ImportError:
        # Fall back to regular Flask server
        print(" * ngrok not available, running on local URL only")
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main() 