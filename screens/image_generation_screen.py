from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QComboBox,
                            QGroupBox, QProgressBar, QMessageBox, QScrollArea,
                            QGridLayout, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QFont, QPixmap, QImage
import os
from PIL import Image
import io

class ImageGenerationWorker(QThread):
    """Worker thread for generating images"""
    finished = pyqtSignal(list)  # List of image paths
    progress = pyqtSignal(int, str)  # Progress percentage, status message
    error = pyqtSignal(str)
    
    def __init__(self, image_service, image_prompts, style):
        super().__init__()
        self.image_service = image_service
        self.image_prompts = image_prompts
        self.style = style
    
    def run(self):
        try:
            # Apply style to prompts if needed
            styled_prompts = []
            for prompt in self.image_prompts:
                # Add style to prompt
                styled_prompt = prompt.copy()
                if 'prompt' in styled_prompt:
                    # Add style keywords based on selected style
                    if self.style == "Cinematic":
                        styled_prompt['prompt'] += ", cinematic lighting, movie scene, 35mm film"
                    elif self.style == "Realistic":
                        styled_prompt['prompt'] += ", photorealistic, detailed, 8k uhd, realistic"
                    elif self.style == "Artistic":
                        styled_prompt['prompt'] += ", artistic, painterly, dramatic, stylized"
                
                styled_prompts.append(styled_prompt)
            
            # Generate images
            total_images = len(styled_prompts)
            for i, _ in enumerate(styled_prompts):
                progress_pct = int((i / total_images) * 100)
                self.progress.emit(progress_pct, f"Generating image {i+1}/{total_images}")
            
            # Generate all images
            image_paths = self.image_service.generate_story_images(styled_prompts)
            
            self.progress.emit(100, "Image generation complete")
            self.finished.emit(image_paths)
            
        except Exception as e:
            self.error.emit(str(e))

class ImageGenerationScreen(QWidget):
    """Screen for generating and previewing images"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.image_paths = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Image Generation")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Style selection
        style_layout = QHBoxLayout()
        style_label = QLabel("Visual Style:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Cinematic", "Realistic", "Artistic"])
        style_layout.addWidget(style_label)
        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()
        main_layout.addLayout(style_layout)
        
        # Generate button
        self.generate_button = QPushButton("Generate Images")
        self.generate_button.clicked.connect(self.on_generate_clicked)
        main_layout.addWidget(self.generate_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to generate images")
        main_layout.addWidget(self.status_label)
        
        # Image preview area
        preview_group = QGroupBox("Generated Images")
        preview_layout = QVBoxLayout()
        
        # Create a scroll area for the images
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create a widget to hold the grid layout
        scroll_content = QWidget()
        self.image_grid = QGridLayout(scroll_content)
        
        scroll_area.setWidget(scroll_content)
        preview_layout.addWidget(scroll_area)
        
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group, 1)  # Give it a stretch factor
        
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
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        
        # Check if we already have scene descriptions
        if self.parent and self.parent.current_project.get('scene_descriptions'):
            # Enable generate button
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setEnabled(False)
            QMessageBox.warning(self, "Warning", "No scene descriptions available. Please go back and generate subtitles first.")
    
    def on_generate_clicked(self):
        """Handle generate button click"""
        if not self.parent:
            return
        
        # Get scene descriptions from project data
        scene_descriptions = self.parent.current_project.get('scene_descriptions')
        if not scene_descriptions:
            QMessageBox.warning(self, "Warning", "No scene descriptions available")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        self.status_label.setText("Initializing image generation...")
        
        # Get selected style
        style = self.style_combo.currentText()
        
        # Create worker thread
        self.worker = ImageGenerationWorker(
            self.parent.image_service,
            scene_descriptions,
            style
        )
        
        # Connect signals
        self.worker.progress.connect(self.on_generation_progress)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        
        # Start worker
        self.worker.start()
    
    def on_generation_progress(self, progress, status):
        """Handle generation progress update"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def on_generation_finished(self, image_paths):
        """Handle generation finished"""
        self.image_paths = image_paths
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Regenerate Images")
        self.status_label.setText(f"Generated {len(image_paths)} images")
        
        # Display images in grid
        self.display_images(image_paths)
        
        # Enable next button
        self.next_button.setEnabled(True)
        
        # Update project data
        if self.parent:
            # Generate image prompts if not already done
            if not self.parent.current_project.get('image_prompts'):
                self.parent.current_project['image_prompts'] = self.parent.current_project['scene_descriptions']
            
            self.parent.current_project['image_paths'] = image_paths
            
        # Show success message
        QMessageBox.information(self, "Success", f"Successfully generated {len(image_paths)} images!")
    
    def display_images(self, image_paths):
        """Display images in the grid layout"""
        # Clear existing items
        while self.image_grid.count():
            item = self.image_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add images to grid
        row, col = 0, 0
        max_cols = 3  # Number of columns in the grid
        
        for i, path in enumerate(image_paths):
            try:
                # Create image label
                img_label = QLabel()
                img_label.setAlignment(Qt.AlignCenter)
                
                # Load and resize image
                pixmap = QPixmap(path)
                pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                img_label.setPixmap(pixmap)
                
                # Add to grid
                self.image_grid.addWidget(img_label, row, col)
                
                # Update row and column
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
            except Exception as e:
                print(f"Error displaying image {path}: {str(e)}")
    
    def on_generation_error(self, error_msg):
        """Handle generation error"""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Images")
        self.status_label.setText("Error generating images")
        
        # Show error message
        QMessageBox.critical(self, "Error", f"Failed to generate images: {error_msg}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('subtitles')
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.parent and self.image_paths:
            self.parent.navigate_to('video_compilation') 