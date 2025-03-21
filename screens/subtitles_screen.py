from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QTextEdit,
                            QGroupBox, QProgressBar, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
import os

class SubtitleGenerationWorker(QThread):
    """Worker thread for generating subtitles"""
    finished = pyqtSignal(str)  # Path to generated SRT file
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, audio_service, audio_path):
        super().__init__()
        self.audio_service = audio_service
        self.audio_path = audio_path
    
    def run(self):
        try:
            # Generate subtitles
            self.progress.emit(10)
            srt_path = self.audio_service.generate_subtitles(self.audio_path)
            
            if srt_path:
                self.progress.emit(100)
                self.finished.emit(srt_path)
            else:
                self.error.emit("Failed to generate subtitles")
        except Exception as e:
            self.error.emit(str(e))

class SubtitlesScreen(QWidget):
    """Screen for generating and previewing subtitles"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.srt_path = None
        self.subtitle_segments = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Subtitle Generation")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Generate button
        self.generate_button = QPushButton("Generate Subtitles")
        self.generate_button.clicked.connect(self.on_generate_clicked)
        main_layout.addWidget(self.generate_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Subtitle preview
        subtitle_group = QGroupBox("Subtitle Preview")
        subtitle_layout = QVBoxLayout()
        
        self.subtitle_list = QListWidget()
        subtitle_layout.addWidget(self.subtitle_list)
        
        subtitle_group.setLayout(subtitle_layout)
        main_layout.addWidget(subtitle_group)
        
        # Export button
        self.export_button = QPushButton("Export Subtitles")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.on_export_clicked)
        main_layout.addWidget(self.export_button)
        
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
        
        # Check if we already have audio path
        if self.parent and self.parent.current_project.get('audio_path'):
            audio_path = self.parent.current_project['audio_path']
            if os.path.exists(audio_path):
                # Enable generate button
                self.generate_button.setEnabled(True)
            else:
                self.generate_button.setEnabled(False)
                QMessageBox.warning(self, "Warning", "Audio file not found. Please go back and regenerate narration.")
    
    def on_generate_clicked(self):
        """Handle generate subtitles button click"""
        if not self.parent or not self.parent.current_project.get('audio_path'):
            QMessageBox.warning(self, "Warning", "No audio file available")
            return
        
        audio_path = self.parent.current_project['audio_path']
        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "Warning", "Audio file not found")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        # Create worker thread
        self.worker = SubtitleGenerationWorker(
            self.parent.audio_service,
            audio_path
        )
        
        # Connect signals
        self.worker.finished.connect(self.on_subtitles_generated)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.on_generation_error)
        
        # Start worker
        self.worker.start()
    
    def on_subtitles_generated(self, srt_path):
        """Handle generated subtitles"""
        self.srt_path = srt_path
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Regenerate Subtitles")
        
        # Parse SRT file and populate list
        self.subtitle_segments = self.parent.audio_service.parse_srt_timestamps(srt_path)
        self.populate_subtitle_list()
        
        # Enable export and next buttons
        self.export_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        # Update project data
        if self.parent:
            self.parent.current_project['subtitles_path'] = srt_path
            
        # Show success message
        QMessageBox.information(self, "Success", "Subtitles generated successfully!")
    
    def populate_subtitle_list(self):
        """Populate the subtitle list with segments"""
        self.subtitle_list.clear()
        
        for segment in self.subtitle_segments:
            item_text = f"{segment['start_time']} --> {segment['end_time']}\n{segment['text']}"
            item = QListWidgetItem(item_text)
            self.subtitle_list.addItem(item)
    
    def on_generation_error(self, error_msg):
        """Handle generation error"""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Subtitles")
        
        # Show error message
        QMessageBox.critical(self, "Error", f"Failed to generate subtitles: {error_msg}")
    
    def on_export_clicked(self):
        """Handle export subtitles button click"""
        if not self.srt_path or not os.path.exists(self.srt_path):
            QMessageBox.warning(self, "Warning", "No subtitle file available")
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
                import shutil
                shutil.copy2(self.srt_path, export_path)
                QMessageBox.information(self, "Success", f"Subtitles exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export subtitles: {str(e)}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('narration')
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.parent and self.srt_path:
            # Generate scene descriptions before moving to next screen
            if self.subtitle_segments:
                try:
                    # Show progress dialog
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setValue(0)
                    self.next_button.setEnabled(False)
                    
                    # Generate scene descriptions
                    scene_descriptions = self.parent.ai_service.generate_scene_descriptions(
                        self.subtitle_segments
                    )
                    
                    # Update project data
                    self.parent.current_project['scene_descriptions'] = scene_descriptions
                    
                    # Hide progress
                    self.progress_bar.setVisible(False)
                    self.next_button.setEnabled(True)
                    
                    # Navigate to next screen
                    self.parent.navigate_to('image_generation')
                except Exception as e:
                    self.progress_bar.setVisible(False)
                    self.next_button.setEnabled(True)
                    QMessageBox.critical(self, "Error", f"Failed to generate scene descriptions: {str(e)}")
            else:
                QMessageBox.warning(self, "Warning", "No subtitle segments available") 