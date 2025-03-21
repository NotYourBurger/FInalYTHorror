import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt, QSettings

# Import UI screens
from screens.home_screen import HomeScreen
from screens.story_selection_screen import StorySelectionScreen
from screens.narration_screen import NarrationScreen
from screens.subtitles_screen import SubtitlesScreen
from screens.image_generation_screen import ImageGenerationScreen
from screens.video_compilation_screen import VideoCompilationScreen
from screens.export_screen import ExportScreen

# Import backend services
from services.reddit_service import RedditService
from services.ai_service import AIService
from services.audio_service import AudioService
from services.image_service import ImageService
from services.video_service import VideoService

# Import credentials
try:
    from credentials_template import (
        REDDIT_CLIENT_ID, 
        REDDIT_CLIENT_SECRET, 
        REDDIT_USER_AGENT,
        GEMINI_API_KEY
    )
except ImportError:
    # Default credentials if file not found
    REDDIT_CLIENT_ID = "Jf3jkA3Y0dBCfluYvS8aVw"
    REDDIT_CLIENT_SECRET = "1dWKIP6ME7FBR66motXS6273rkkf0g"
    REDDIT_USER_AGENT = "Horror Stories by Wear_Severe"
    GEMINI_API_KEY = "AIzaSyD_vBSluRNPI6z7JoKfl67M6D3DCq4l0NI"

class HorrorStoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Horror Story Generator")
        self.resize(1200, 800)
        
        # Initialize settings
        self.settings = QSettings("HorrorStoryAI", "HorrorStoryGenerator")
        
        # Initialize services
        self.init_services()
        
        # Initialize UI
        self.init_ui()
        
        # Project data
        self.current_project = None
        
    def init_services(self):
        """Initialize backend services"""
        # Initialize Reddit service
        self.reddit_service = RedditService(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        # Initialize AI service
        self.ai_service = AIService(
            api_key=GEMINI_API_KEY
        )
        
        # Initialize other services
        self.audio_service = AudioService()
        self.image_service = ImageService()
        self.video_service = VideoService()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Central widget
        central_widget = QStackedWidget()
        self.setCentralWidget(central_widget)
        
        # Create screens
        self.home_screen = HomeScreen(self)
        self.story_selection_screen = StorySelectionScreen(self)
        self.narration_screen = NarrationScreen(self)
        self.subtitles_screen = SubtitlesScreen(self)
        self.image_generation_screen = ImageGenerationScreen(self)
        self.video_compilation_screen = VideoCompilationScreen(self)
        self.export_screen = ExportScreen(self)
        
        # Add screens to stacked widget
        central_widget.addWidget(self.home_screen)
        central_widget.addWidget(self.story_selection_screen)
        central_widget.addWidget(self.narration_screen)
        central_widget.addWidget(self.subtitles_screen)
        central_widget.addWidget(self.image_generation_screen)
        central_widget.addWidget(self.video_compilation_screen)
        central_widget.addWidget(self.export_screen)
        
        # Store reference to stacked widget
        self.stacked_widget = central_widget
        
        # Start with home screen
        self.stacked_widget.setCurrentWidget(self.home_screen)
    
    def navigate_to(self, screen_name):
        """Navigate to a specific screen"""
        screen_map = {
            'home': self.home_screen,
            'story_selection': self.story_selection_screen,
            'narration': self.narration_screen,
            'subtitles': self.subtitles_screen,
            'image_generation': self.image_generation_screen,
            'video_compilation': self.video_compilation_screen,
            'export': self.export_screen
        }
        
        if screen_name in screen_map:
            self.stacked_widget.setCurrentWidget(screen_map[screen_name])
        
    def start_new_project(self):
        """Start a new project and navigate to story selection"""
        self.current_project = {
            'story_data': None,
            'audio_path': None,
            'subtitles_path': None,
            'scene_descriptions': None,
            'image_prompts': None,
            'image_paths': None,
            'video_path': None
        }
        self.navigate_to('story_selection')
        
    def load_project(self, project_path):
        """Load an existing project"""
        # TODO: Implement project loading
        pass
        
    def save_project(self):
        """Save the current project"""
        # TODO: Implement project saving
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set application-wide stylesheet for dark theme
    try:
        with open("assets/style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: style.qss not found. Using default style.")
    
    window = HorrorStoryApp()
    window.show()
    sys.exit(app.exec_()) 