from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class HomeScreen(QWidget):
    """Home screen for the Horror Story Generator app"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Horror Story Generator")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 24, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Create cinematic horror videos with AI")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Arial", 14)
        subtitle_label.setFont(subtitle_font)
        main_layout.addWidget(subtitle_label)
        
        # Spacer
        main_layout.addSpacing(40)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # New Project button
        new_project_btn = QPushButton("Start New Project")
        new_project_btn.setMinimumHeight(60)
        new_project_btn.setFont(QFont("Arial", 12))
        new_project_btn.clicked.connect(self.on_new_project_clicked)
        buttons_layout.addWidget(new_project_btn)
        
        # Load Project button
        load_project_btn = QPushButton("Load Existing Project")
        load_project_btn.setMinimumHeight(60)
        load_project_btn.setFont(QFont("Arial", 12))
        load_project_btn.clicked.connect(self.on_load_project_clicked)
        buttons_layout.addWidget(load_project_btn)
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setMinimumHeight(60)
        settings_btn.setFont(QFont("Arial", 12))
        settings_btn.clicked.connect(self.on_settings_clicked)
        buttons_layout.addWidget(settings_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Spacer
        main_layout.addSpacing(40)
        
        # Recent projects section
        recent_label = QLabel("Recent Projects")
        recent_label.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(recent_label)
        
        # Recent projects list
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setMaximumHeight(200)
        self.recent_projects_list.itemDoubleClicked.connect(self.on_recent_project_clicked)
        main_layout.addWidget(self.recent_projects_list)
        
        # Populate with dummy data for now
        self.populate_recent_projects()
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def populate_recent_projects(self):
        """Populate the recent projects list"""
        # This would normally load from settings or a database
        # For now, just add some dummy items
        self.recent_projects_list.clear()
        
        # Check if we have any recent projects in settings
        recent_projects = self.parent.settings.value("recent_projects", [])
        
        if not recent_projects:
            # Add a placeholder item
            item = QListWidgetItem("No recent projects")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.recent_projects_list.addItem(item)
        else:
            # Add actual recent projects
            for project in recent_projects:
                self.recent_projects_list.addItem(project)
    
    def on_new_project_clicked(self):
        """Handle new project button click"""
        if self.parent:
            self.parent.start_new_project()
    
    def on_load_project_clicked(self):
        """Handle load project button click"""
        # Open file dialog to select project file
        project_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Horror Story Project",
            "",
            "Horror Story Project Files (*.hsproject);;All Files (*)"
        )
        
        if project_path:
            if self.parent:
                self.parent.load_project(project_path)
    
    def on_settings_clicked(self):
        """Handle settings button click"""
        # TODO: Implement settings dialog
        pass
    
    def on_recent_project_clicked(self, item):
        """Handle recent project item click"""
        project_path = item.text()
        if self.parent and project_path != "No recent projects":
            self.parent.load_project(project_path) 