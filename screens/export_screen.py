from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QFileDialog,
                            QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import os
import shutil

class ExportScreen(QWidget):
    """Screen for exporting and sharing the final project"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Export Project")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Project summary
        summary_group = QGroupBox("Project Summary")
        summary_layout = QVBoxLayout()
        
        self.title_label = QLabel("Title: ")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        summary_layout.addWidget(self.title_label)
        
        self.duration_label = QLabel("Duration: ")
        summary_layout.addWidget(self.duration_label)
        
        self.files_label = QLabel("Generated Files: ")
        summary_layout.addWidget(self.files_label)
        
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout()
        
        # Video export
        video_export_btn = QPushButton("Export Video")
        video_export_btn.clicked.connect(self.on_export_video)
        export_layout.addWidget(video_export_btn)
        
        # Audio export
        audio_export_btn = QPushButton("Export Audio")
        audio_export_btn.clicked.connect(self.on_export_audio)
        export_layout.addWidget(audio_export_btn)
        
        # Subtitles export
        subtitles_export_btn = QPushButton("Export Subtitles")
        subtitles_export_btn.clicked.connect(self.on_export_subtitles)
        export_layout.addWidget(subtitles_export_btn)
        
        # Images export
        images_export_btn = QPushButton("Export Images")
        images_export_btn.clicked.connect(self.on_export_images)
        export_layout.addWidget(images_export_btn)
        
        # Full project export
        project_export_btn = QPushButton("Export Complete Project")
        project_export_btn.clicked.connect(self.on_export_project)
        export_layout.addWidget(project_export_btn)
        
        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.on_back_clicked)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        new_project_button = QPushButton("Start New Project")
        new_project_button.clicked.connect(self.on_new_project_clicked)
        nav_layout.addWidget(new_project_button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        
        # Update project summary
        self.update_project_summary()
    
    def update_project_summary(self):
        """Update the project summary labels"""
        if not self.parent or not self.parent.current_project:
            return
        
        project = self.parent.current_project
        
        # Update title
        if project.get('story_data') and 'title' in project['story_data']:
            self.title_label.setText(f"Title: {project['story_data']['title']}")
        else:
            self.title_label.setText("Title: Untitled Horror Story")
        
        # Update duration
        duration_text = "Unknown"
        if project.get('video_path'):
            try:
                from moviepy.editor import VideoFileClip
                clip = VideoFileClip(project['video_path'])
                duration_text = f"{int(clip.duration // 60)}m {int(clip.duration % 60)}s"
                clip.close()
            except:
                pass
        self.duration_label.setText(f"Duration: {duration_text}")
        
        # Update files
        files_text = ""
        if project.get('video_path'):
            files_text += "Video, "
        if project.get('audio_path'):
            files_text += "Audio, "
        if project.get('subtitles_path'):
            files_text += "Subtitles, "
        if project.get('image_paths'):
            files_text += f"{len(project['image_paths'])} Images"
        
        if not files_text:
            files_text = "None"
        else:
            files_text = files_text.rstrip(", ")
        
        self.files_label.setText(f"Generated Files: {files_text}")
    
    def on_export_video(self):
        """Handle export video button click"""
        if not self.parent or not self.parent.current_project.get('video_path'):
            QMessageBox.warning(self, "Warning", "No video file available")
            return
        
        video_path = self.parent.current_project['video_path']
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Warning", "Video file not found")
            return
        
        # Open file dialog to select export location
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Video",
            "",
            "MP4 Files (*.mp4);;All Files (*)"
        )
        
        if export_path:
            try:
                shutil.copy2(video_path, export_path)
                QMessageBox.information(self, "Success", f"Video exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export video: {str(e)}")
    
    def on_export_audio(self):
        """Handle export audio button click"""
        if not self.parent or not self.parent.current_project.get('audio_path'):
            QMessageBox.warning(self, "Warning", "No audio file available")
            return
        
        audio_path = self.parent.current_project['audio_path']
        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "Warning", "Audio file not found")
            return
        
        # Open file dialog to select export location
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audio",
            "",
            "WAV Files (*.wav);;All Files (*)"
        )
        
        if export_path:
            try:
                shutil.copy2(audio_path, export_path)
                QMessageBox.information(self, "Success", f"Audio exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export audio: {str(e)}")
    
    def on_export_subtitles(self):
        """Handle export subtitles button click"""
        if not self.parent or not self.parent.current_project.get('subtitles_path'):
            QMessageBox.warning(self, "Warning", "No subtitles file available")
            return
        
        subtitles_path = self.parent.current_project['subtitles_path']
        if not os.path.exists(subtitles_path):
            QMessageBox.warning(self, "Warning", "Subtitles file not found")
            return
        
        # Open file dialog to select export location
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Subtitles",
            "",
            "SRT Files (*.srt);;All Files (*)"
        )
        
        if export_path:
            try:
                shutil.copy2(subtitles_path, export_path)
                QMessageBox.information(self, "Success", f"Subtitles exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export subtitles: {str(e)}")
    
    def on_export_images(self):
        """Handle export images button click"""
        if not self.parent or not self.parent.current_project.get('image_paths'):
            QMessageBox.warning(self, "Warning", "No image files available")
            return
        
        image_paths = self.parent.current_project['image_paths']
        if not image_paths:
            QMessageBox.warning(self, "Warning", "No image files found")
            return
        
        # Open file dialog to select export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            ""
        )
        
        if export_dir:
            try:
                # Create images directory
                images_dir = os.path.join(export_dir, "horror_story_images")
                os.makedirs(images_dir, exist_ok=True)
                
                # Copy images
                for i, path in enumerate(image_paths):
                    if os.path.exists(path):
                        filename = f"scene_{i+1:03d}.png"
                        shutil.copy2(path, os.path.join(images_dir, filename))
                
                QMessageBox.information(self, "Success", f"Images exported to {images_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export images: {str(e)}")
    
    def on_export_project(self):
        """Handle export complete project button click"""
        if not self.parent or not self.parent.current_project:
            QMessageBox.warning(self, "Warning", "No project data available")
            return
        
        # Open file dialog to select export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            ""
        )
        
        if export_dir:
            try:
                # Create project directory
                project_name = "horror_story_project"
                if self.parent.current_project.get('story_data') and 'title' in self.parent.current_project['story_data']:
                    # Create safe filename from title
                    import re
                    project_name = re.sub(r'[^\w\s-]', '', self.parent.current_project['story_data']['title'])
                    project_name = re.sub(r'[-\s]+', '_', project_name).strip('-_').lower()
                
                project_dir = os.path.join(export_dir, project_name)
                os.makedirs(project_dir, exist_ok=True)
                
                # Create subdirectories
                os.makedirs(os.path.join(project_dir, "video"), exist_ok=True)
                os.makedirs(os.path.join(project_dir, "audio"), exist_ok=True)
                os.makedirs(os.path.join(project_dir, "subtitles"), exist_ok=True)
                os.makedirs(os.path.join(project_dir, "images"), exist_ok=True)
                
                # Copy files
                project = self.parent.current_project
                
                # Copy video
                if project.get('video_path') and os.path.exists(project['video_path']):
                    shutil.copy2(project['video_path'], os.path.join(project_dir, "video", "final_video.mp4"))
                
                # Copy audio
                if project.get('audio_path') and os.path.exists(project['audio_path']):
                    shutil.copy2(project['audio_path'], os.path.join(project_dir, "audio", "narration.wav"))
                
                # Copy subtitles
                if project.get('subtitles_path') and os.path.exists(project['subtitles_path']):
                    shutil.copy2(project['subtitles_path'], os.path.join(project_dir, "subtitles", "subtitles.srt"))
                
                # Copy images
                if project.get('image_paths'):
                    for i, path in enumerate(project['image_paths']):
                        if os.path.exists(path):
                            filename = f"scene_{i+1:03d}.png"
                            shutil.copy2(path, os.path.join(project_dir, "images", filename))
                
                # Create README file
                with open(os.path.join(project_dir, "README.txt"), 'w') as f:
                    f.write(f"Horror Story Project: {self.title_label.text()[7:]}\n")
                    f.write(f"Duration: {self.duration_label.text()[10:]}\n\n")
                    f.write("Generated with Horror Story Generator\n\n")
                    f.write("Project Contents:\n")
                    f.write("- video/final_video.mp4: The final horror video\n")
                    f.write("- audio/narration.wav: The narration audio\n")
                    f.write("- subtitles/subtitles.srt: The subtitle file\n")
                    f.write("- images/: Generated scene images\n")
                
                QMessageBox.information(self, "Success", f"Project exported to {project_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export project: {str(e)}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('video_compilation')
    
    def on_new_project_clicked(self):
        """Handle new project button click"""
        if self.parent:
            # Confirm with user
            reply = QMessageBox.question(
                self, 
                "Start New Project", 
                "Are you sure you want to start a new project? Current project data will be lost.",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.parent.start_new_project() 