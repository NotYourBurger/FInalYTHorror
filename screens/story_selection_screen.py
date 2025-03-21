from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QTextEdit,
                            QComboBox, QCheckBox, QSpinBox, QGroupBox, QSplitter,
                            QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import random

class StoryFetchWorker(QThread):
    """Worker thread for fetching stories"""
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, reddit_service, subreddits, min_length):
        super().__init__()
        self.reddit_service = reddit_service
        self.subreddits = subreddits
        self.min_length = min_length
    
    def run(self):
        try:
            # Fetch stories
            stories = self.reddit_service.fetch_stories(
                subreddits=self.subreddits,
                min_length=self.min_length
            )
            self.finished.emit(stories)
        except Exception as e:
            self.error.emit(str(e))

class StorySelectionScreen(QWidget):
    """Screen for selecting and enhancing horror stories"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.stories = []
        self.selected_story = None
        self.enhanced_story = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Story Selection")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Story selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Subreddit selection
        subreddit_group = QGroupBox("Subreddit Selection")
        subreddit_layout = QVBoxLayout()
        
        self.subreddit_checkboxes = []
        if self.parent and hasattr(self.parent, 'reddit_service'):
            subreddits = self.parent.reddit_service.get_subreddit_list()
            for subreddit in subreddits:
                checkbox = QCheckBox(f"r/{subreddit}")
                # Select some by default
                if subreddit in ["nosleep", "shortscarystories"]:
                    checkbox.setChecked(True)
                self.subreddit_checkboxes.append((subreddit, checkbox))
                subreddit_layout.addWidget(checkbox)
        
        subreddit_group.setLayout(subreddit_layout)
        left_layout.addWidget(subreddit_group)
        
        # Story length
        length_layout = QHBoxLayout()
        length_label = QLabel("Minimum story length:")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(500, 10000)
        self.length_spinbox.setSingleStep(500)
        self.length_spinbox.setValue(1000)
        length_layout.addWidget(length_label)
        length_layout.addWidget(self.length_spinbox)
        left_layout.addLayout(length_layout)
        
        # Fetch button
        self.fetch_button = QPushButton("Fetch Stories")
        self.fetch_button.clicked.connect(self.on_fetch_clicked)
        left_layout.addWidget(self.fetch_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Story list
        self.story_list = QListWidget()
        self.story_list.itemClicked.connect(self.on_story_selected)
        left_layout.addWidget(self.story_list)
        
        # Right panel - Story preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Story title
        self.story_title_label = QLabel("Select a story to preview")
        self.story_title_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(self.story_title_label)
        
        # Story content
        self.story_content = QTextEdit()
        self.story_content.setReadOnly(True)
        right_layout.addWidget(self.story_content)
        
        # Enhance button
        self.enhance_button = QPushButton("Enhance Story")
        self.enhance_button.clicked.connect(self.on_enhance_clicked)
        self.enhance_button.setEnabled(False)
        right_layout.addWidget(self.enhance_button)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])  # Initial sizes
        
        main_layout.addWidget(splitter)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.on_back_clicked)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.next_button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def on_fetch_clicked(self):
        """Handle fetch stories button click"""
        # Get selected subreddits
        selected_subreddits = [
            subreddit for subreddit, checkbox in self.subreddit_checkboxes
            if checkbox.isChecked()
        ]
        
        if not selected_subreddits:
            # If none selected, use default
            selected_subreddits = ["nosleep", "shortscarystories"]
        
        # Get minimum length
        min_length = self.length_spinbox.value()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.fetch_button.setEnabled(False)
        
        # Create worker thread
        self.worker = StoryFetchWorker(
            self.parent.reddit_service,
            selected_subreddits,
            min_length
        )
        
        # Connect signals
        self.worker.finished.connect(self.on_stories_fetched)
        self.worker.error.connect(self.on_fetch_error)
        
        # Start worker
        self.worker.start()
    
    def on_stories_fetched(self, stories):
        """Handle fetched stories"""
        self.stories = stories
        self.progress_bar.setVisible(False)
        self.fetch_button.setEnabled(True)
        
        # Populate story list
        self.story_list.clear()
        for story in stories:
            item = QListWidgetItem(story.title)
            item.setData(Qt.UserRole, story.id)
            self.story_list.addItem(item)
    
    def on_fetch_error(self, error_msg):
        """Handle fetch error"""
        self.progress_bar.setVisible(False)
        self.fetch_button.setEnabled(True)
        # TODO: Show error message
        print(f"Error fetching stories: {error_msg}")
    
    def on_story_selected(self, item):
        """Handle story selection"""
        story_id = item.data(Qt.UserRole)
        
        # Find the selected story
        for story in self.stories:
            if story.id == story_id:
                self.selected_story = story
                break
        
        if self.selected_story:
            # Update UI
            self.story_title_label.setText(self.selected_story.title)
            self.story_content.setText(self.selected_story.selftext)
            self.enhance_button.setEnabled(True)
    
    def on_enhance_clicked(self):
        """Handle enhance story button click"""
        if not self.selected_story:
            return
        
        # Disable button during enhancement
        self.enhance_button.setEnabled(False)
        self.enhance_button.setText("Enhancing...")
        
        # Enhance the story using AI service
        try:
            enhanced_text = self.parent.ai_service.enhance_story(self.selected_story.selftext)
            
            # Update UI
            self.story_content.setText(enhanced_text)
            self.enhanced_story = enhanced_text
            
            # Enable next button
            self.next_button.setEnabled(True)
            
            # Mark story as used
            self.parent.reddit_service.mark_story_used(self.selected_story.id)
            
            # Update project data
            self.parent.current_project['story_data'] = {
                'title': self.selected_story.title,
                'original': self.selected_story.selftext,
                'enhanced': enhanced_text,
                'subreddit': self.selected_story.subreddit.display_name,
                'story_id': self.selected_story.id
            }
            
            # Re-enable enhance button
            self.enhance_button.setText("Re-Enhance Story")
            self.enhance_button.setEnabled(True)
            
        except Exception as e:
            print(f"Error enhancing story: {str(e)}")
            self.enhance_button.setText("Enhance Story")
            self.enhance_button.setEnabled(True)
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('home')
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.parent and self.enhanced_story:
            self.parent.navigate_to('narration') 