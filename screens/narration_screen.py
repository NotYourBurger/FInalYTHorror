from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QComboBox, QGroupBox, QProgressBar,
                            QTextEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
import os

class NarrationGenerationWorker(QThread):
    """Worker thread for generating narration audio"""
    finished = pyqtSignal(str)  # Path to generated audio
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, audio_service, script_text, voice, speed):
        super().__init__()
        self.audio_service = audio_service
        self.script_text = script_text
        self.voice = voice
        self.speed = speed
    
    def run(self):
        try:
            # Generate narration
            audio_path = self.audio_service.generate_narration(
                self.script_text,
                voice=self.voice,
                speed=self.speed
            )
            
            if audio_path:
                self.finished.emit(audio_path)
            else:
                self.error.emit("Failed to generate audio narration")
        except Exception as e:
            self.error.emit(str(e))

class NarrationScreen(QWidget):
    """Screen for generating and previewing narration audio"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.audio_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Voice Narration")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Script preview
        script_group = QGroupBox("Script Preview")
        script_layout = QVBoxLayout()
        
        self.script_preview = QTextEdit()
        self.script_preview.setReadOnly(True)
        script_layout.addWidget(self.script_preview)
        
        script_group.setLayout(script_layout)
        main_layout.addWidget(script_group)
        
        # Voice settings
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()
        
        # Voice selection
        voice_selection_layout = QHBoxLayout()
        voice_label = QLabel("Narrator Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["af_bella", "en_joe", "en_emily"])
        self.voice_combo.setCurrentText("af_bella")  # Default horror voice
        voice_selection_layout.addWidget(voice_label)
        voice_selection_layout.addWidget(self.voice_combo)
        voice_layout.addLayout(voice_selection_layout)
        
        # Speed slider
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Narration Speed:")
        self.speed_value_label = QLabel("0.85")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 120)
        self.speed_slider.setValue(85)  # Default 0.85
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        voice_layout.addLayout(speed_layout)
        
        voice_group.setLayout(voice_layout)
        main_layout.addWidget(voice_group)
        
        # Generate button
        self.generate_button = QPushButton("Generate Narration")
        self.generate_button.clicked.connect(self.on_generate_clicked)
        main_layout.addWidget(self.generate_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Audio preview controls
        preview_group = QGroupBox("Audio Preview")
        preview_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.on_play_clicked)
        preview_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        preview_layout.addWidget(self.stop_button)
        
        self.export_button = QPushButton("Export Audio")
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
        
        # Load script from project data
        if self.parent and self.parent.current_project.get('story_data'):
            story_data = self.parent.current_project['story_data']
            if 'enhanced' in story_data:
                self.script_preview.setText(story_data['enhanced'])
    
    def update_speed_label(self, value):
        """Update the speed value label"""
        speed = value / 100.0
        self.speed_value_label.setText(f"{speed:.2f}")
    
    def on_generate_clicked(self):
        """Handle generate narration button click"""
        # Get script text
        script_text = self.script_preview.toPlainText()
        if not script_text:
            QMessageBox.warning(self, "Warning", "No script text available")
            return
        
        # Get voice settings
        voice = self.voice_combo.currentText()
        speed = float(self.speed_value_label.text())
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        # Create worker thread
        self.worker = NarrationGenerationWorker(
            self.parent.audio_service,
            script_text,
            voice,
            speed
        )
        
        # Connect signals
        self.worker.finished.connect(self.on_narration_generated)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.on_generation_error)
        
        # Start worker
        self.worker.start()
    
    def on_narration_generated(self, audio_path):
        """Handle generated narration"""
        self.audio_path = audio_path
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Regenerate Narration")
        
        # Enable audio controls
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.next_button.setEnabled(True)
        
        # Update project data
        if self.parent:
            self.parent.current_project['audio_path'] = audio_path
            
        # Show success message
        QMessageBox.information(self, "Success", "Narration generated successfully!")
    
    def on_generation_error(self, error_msg):
        """Handle generation error"""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Narration")
        
        # Show error message
        QMessageBox.critical(self, "Error", f"Failed to generate narration: {error_msg}")
    
    def on_play_clicked(self):
        """Handle play button click"""
        if not self.audio_path or not os.path.exists(self.audio_path):
            QMessageBox.warning(self, "Warning", "No audio file available")
            return
        
        # Play audio using system default player
        try:
            import platform
            import subprocess
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', self.audio_path))
            elif platform.system() == 'Windows':
                os.startfile(self.audio_path)
            else:  # Linux
                subprocess.call(('xdg-open', self.audio_path))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play audio: {str(e)}")
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        # This is a placeholder - in a real app, you'd need to
        # implement proper audio playback control
        pass
    
    def on_export_clicked(self):
        """Handle export audio button click"""
        if not self.audio_path or not os.path.exists(self.audio_path):
            QMessageBox.warning(self, "Warning", "No audio file available")
            return
        
        # Open file dialog to select export location
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Narration Audio",
            "",
            "WAV Files (*.wav);;All Files (*)"
        )
        
        if export_path:
            try:
                import shutil
                shutil.copy2(self.audio_path, export_path)
                QMessageBox.information(self, "Success", f"Audio exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export audio: {str(e)}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        if self.parent:
            self.parent.navigate_to('story_selection')
    
    def on_next_clicked(self):
        """Handle next button click"""
        if self.parent and self.audio_path:
            self.parent.navigate_to('subtitles') 