#!/usr/bin/env python3
"""
Setup script for Horror Story Generator
Creates necessary directories and files
"""

import os
import sys

def create_directory_structure():
    """Create the necessary directory structure for the application"""
    directories = [
        "output/audio",
        "output/subtitles",
        "output/images",
        "output/videos",
        "output/temp",
        "data",
        "assets/icons",
        "screens",
        "services"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create .gitkeep file to ensure directory is tracked by git
        with open(os.path.join(directory, ".gitkeep"), "w") as f:
            pass
    
    print("Directory structure created successfully!")

def create_empty_files():
    """Create empty files for the application"""
    files = [
        "data/used_story_ids.txt"
    ]
    
    for file_path in files:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Create empty file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass
    
    print("Empty files created successfully!")

def main():
    """Main function"""
    print("Setting up Horror Story Generator...")
    
    create_directory_structure()
    create_empty_files()
    
    print("\nSetup completed successfully!")
    print("\nTo run the application, use: python main.py")

if __name__ == "__main__":
    main() 