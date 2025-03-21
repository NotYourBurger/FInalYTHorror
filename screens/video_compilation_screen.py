from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QComboBox, QGroupBox, QProgressBar,
                            QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
import os

class VideoCompilationWorker(QThread):
    """Worker thread for compiling video"""
    finished = pyqtSignal(str)  # Path to generated video
    progress = pyqtSignal(int, str)  # Progress percentage, status message
    error = pyqtSignal(str)
    
    def __init__(self, video_service, image_prompts, image_paths, audio_path, 
                 title, srt_path, ambient_path, video_quality, cinematic_ratio, 
                 use_dust_overlay):
        super().__init__()
        self.video_service = video_service
        self.image_prompts = image_prompts
        self.image_paths = image_paths
        self.audio_path = audio_path
        self.title = title
        self.srt_path = srt_path
        self.ambient_path = ambient_path
        self.video_quality = video_quality
        self.cinematic_ratio = cinematic_ratio
        self.use_dust_overlay = use_dust_overlay
    
    def run(self):
        try:
            # Update progress
            self.progress.emit(10, "Starting video compilation...")
            
            # Create video
            video_path = self.video_service.create_video(
                self.image_prompts,
                self.image_paths,
                self.audio_path,
                self.title,
                srt_path=self.srt_path,
                ambient_path=self.ambient_path,
                video_quality=self.video_quality,
                cinematic_ratio=self.cinematic_ratio,
                use_dust_overlay=self.use_dust_overlay
            )
            
            if video_path:
                self.progress.emit(100, "Video compilation complete")
                self.finished.emit(video_path)
            else:
                self.error.emit("Failed to compile video")
        except Exception as e:
            self.error.emit(str(e))

class VideoCompilationScreen(QWidget):
    """Screen for compiling and previewing video"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.video_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Video Compilation")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Video settings
        settings_group = QGroupBox("Video Settings")
        settings_layout = QVBoxLayout()
        
        # Video quality
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Video Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low (2000k)", "Medium (4000k)", "High (6000k)", "Ultra (8000k)"])
        self.quality_combo.setCurrentText("Medium (4000k)")
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        settings_layout.addLayout(quality_layout)
        
        # Cinematic ratio
        ratio_layout = QHBoxLayout()
        ratio_label = QLabel("Aspect Ratio:")
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["16:9 (Widescreen)", "2.35:1 (Cinematic)", "1:1 (Square)"])
        ratio_layout.addWidget(ratio_label)
        ratio_layout.addWidget(self.ratio_combo)
        settings_layout.addLayout(ratio_layout)
        
        # Effects
        effects_layout = QHBoxLayout()
        self.dust_checkbox = QCheckBox("Add Dust Overlay Effect")
        self.dust_checkbox.setChecked(True)
        effects_layout.addWidget(self.dust_checkbox)
        settings_layout.addLayout(effects_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Generate button
        self.compile_button = QPushButton("Compile Video")
        self.compile_button.clicked.connect(self.on_compile_clicked)
        main_layout.addWidget(self.compile_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        
        # Video preview controls
        preview_group = QGroupBox("Video Preview")
        preview_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play Video")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.on_play_clicked)
        preview_layout.addWidget(self.play_button)
        
        self.export_button = QPushButton("Export Video")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.on_export_clicked)
        preview_layout.addWidget(self.export_button)
        
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.on_back_clicked)
        nav_layout.addWidget(back_button)
        
        nav_layout.addStretch()
        
        self.next_button = QPushButton("Finish")
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.next_button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        
        # Check if we have all required data
        if self.parent:
            project = self.parent.current_project
            if (project.get('image_paths') and project.get('audio_path') and 
                project.get('subtitles_path') and project.get('story_data')):
                self.compile_button.setEnabled(True)
            else:
                self.compile_button.setEnabled(False)
                missing = []
                if not project.get('image_paths'):
                    missing.append("images")
                if not project.get('audio_path'):
                    missing.append("audio narration")
                if not project.get('subtitles_path'):
                    missing.append("subtitles")
                
                QMessageBox.warning(self, "Warning", 
                                   f"Missing required data: {', '.join(missing)}. "
                                   "Please go back and complete previous steps.")
    
    def get_video_quality(self):
        """Get video quality bitrate from combo box"""
        quality_text = self.quality_combo.currentText()
        if "Low" in quality_text:
            return "2000k"
        elif "Medium" in quality_text:
            return "4000k"
        elif "High" in quality_text:
            return "6000k"
        elif "Ultra" in quality_text:
            return "8000k"
        return "4000k"  # Default
    
    def get_aspect_ratio(self):
        """Get aspect ratio from combo box"""
        ratio_text = self.ratio_combo.currentText()
        if "16:9" in ratio_text:
            return 16/9
        elif "2.35:1" in ratio_text:
            return 2.35
        elif "1:1" in ratio_text:
            return 1.0
        return 16/9  # Default
    
    def on_compile_clicked(self):
        """Handle compile video button click"""
        if not self.parent:
            return
            
        project = self.parent.current_project
        if not (project.get('image_paths') and project.get('audio_path')):
            QMessageBox.warning(self, "Warning", "Missing required data for video compilation")
            return
        
        # Get settings
        video_quality = self.get_video_quality()
        cinematic_ratio = self.get_aspect_ratio()
        use_dust_overlay = self.dust_checkbox.isChecked()
        
        # Get title from story data
        title = "Horror Story"
        if project.get('story_data') and 'title' in project['story_data']:
            title = project['story_data']['title']
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing video compilation...")
        self.compile_button.setEnabled(False)
        self.compile_button.setText("Compiling...")
        
        # Create worker thread
        self.worker = VideoCompilationWorker(
            self.parent.video_service,
            project.get('image_prompts', []),
            project.get('image_paths', []),
            project.get('audio_path', ''),
            title,
            project.get('subtitles_path', None),
            None,  # Ambient path (not implemented yet)
            video_quality,
            cinematic_ratio,
            use_dust_overlay
        )
        
        # Connect signals
        self.worker.finished.connect(self.on_video_compiled)
        self.worker.progress.connect(self.on_compilation_progress)
        self.worker.error.connect(self.on_compilation_error)
        
        # Start worker
        self.worker.start()
    
    def on_compilation_progress(self, percentage, message):
        """Handle compilation progress updates"""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
    
    def on_video_compiled(self, video_path):
        """Handle compiled video"""
        self.video_path = video_path
        self.progress_bar.setVisible(False)
        self.compile_button.setEnabled(True)
        self.compile_button.setText("Recompile Video")
        self.status_label.setText("Video compilation complete")
        
        # Enable video controls
        self.play_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        # Update project data
        if self.parent:
            self.parent.current_project['video_path'] = video_path
            
        # Show success message
        QMessageBox.information(self, "Success", "Video compiled successfully!")
    
    def on_compilation_error(self, error_msg):
        """Handle compilation error"""
        self.progress_bar.setVisible(False)
        self.compile_button.setEnabled(True)
        self.compile_button.setText("Compile Video")
        self.status_label.setText("Error compiling video")
        
        # Show error message
        QMessageBox.critical(self, "Error", f"Failed to compile video: {error_msg}")
    
    def on_play_clicked(self):
        """Handle play video button click"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "No video file available")
            return
        
        # Play video using system default player
        try:
            import platform
            import subprocess
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', self.video_path))
            elif platform.system() == 'Windows':
                os.startfile(self.video_path)
            else:  # Linux
                subprocess.call(('xdg-open', self.video_path))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play video: {str(e)}")
    
    def on_export_clicked(self):
        """Handle export video button click"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "No video file available")
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
                import shutil
                shutil.copy2(self.video_path, export_path)
                QMessageBox.information(self, "Success", f"Video exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export video: {str(e)}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('image_generation')
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.parent and self.video_path:
            self.parent.navigate_to('export') 