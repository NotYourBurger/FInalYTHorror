#!/usr/bin/env python3
"""
Setup script for Horror Story Video Generator
This script installs all required dependencies with compatible versions
"""

import os
import sys
import subprocess
import time
from typing import List, Dict

def print_step(message: str) -> None:
    """Print a formatted step message"""
    print(f"\n{'='*80}")
    print(f"  {message}")
    print(f"{'='*80}\n")

def run_command(command: List[str], description: str = None) -> bool:
    """Run a shell command and return success status"""
    if description:
        print(f"📦 {description}...")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Success: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Error details: {e.stderr}")
        return False

def install_dependencies() -> bool:
    """Install all required dependencies with compatible versions"""
    print_step("Installing dependencies for Horror Story Video Generator")
    
    # First, uninstall potentially conflicting packages
    run_command(
        ["pip", "uninstall", "-y", "numpy", "diffusers", "transformers", "huggingface_hub"],
        "Removing potentially conflicting packages"
    )
    
    # Install base requirements
    base_packages = [
        "flask",
        "flask-cors",
        "pyngrok",
        "praw",
        "google-generativeai",
        "tqdm",
        "pillow",
        "soundfile",
        "pydub"
    ]
    
    if not run_command(
        ["pip", "install"] + base_packages,
        "Installing base packages"
    ):
        return False
    
    # Install compatible versions of ML packages
    ml_packages = [
        "numpy==1.23.5",
        "torch==1.13.1",
        "huggingface_hub==0.12.0",
        "transformers==4.26.0",
        "diffusers==0.14.0",
        "whisper==1.1.10"
    ]
    
    if not run_command(
        ["pip", "install"] + ml_packages,
        "Installing machine learning packages with compatible versions"
    ):
        return False
    
    print("\n✅ All dependencies installed successfully!")
    return True

def setup_ngrok() -> Dict:
    """Set up ngrok for external access"""
    print_step("Setting up ngrok for external access")
    
    # Install pyngrok if not already installed
    run_command(["pip", "install", "pyngrok"], "Installing pyngrok")
    
    # Import and configure ngrok
    try:
        from pyngrok import ngrok
        
        # Ask for auth token if not provided
        auth_token = os.environ.get("NGROK_AUTH_TOKEN")
        if not auth_token:
            auth_token = input("\n🔑 Please enter your ngrok auth token (from https://dashboard.ngrok.com/get-started/your-authtoken): ")
            if not auth_token:
                auth_token = "2kjfVhuL1QZI4wwCIOOAe6pgunk_7dCPcQqfiBkjLzFduLRQU"  # Default token
        
        # Set auth token
        ngrok.set_auth_token(auth_token)
        
        # Start ngrok tunnel
        port = 5000
        public_url = ngrok.connect(port).public_url
        
        print("\n" + "="*50)
        print(f"✅ NGROK PUBLIC URL: {public_url}")
        print(f"📱 You can access this URL from your phone or any device")
        print("="*50 + "\n")
        
        return {
            "success": True,
            "public_url": public_url,
            "port": port
        }
    
    except Exception as e:
        print(f"❌ Error setting up ngrok: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def check_environment() -> Dict:
    """Check if running in Google Colab or local environment"""
    try:
        import google.colab
        return {
            "environment": "colab",
            "message": "Running in Google Colab environment"
        }
    except ImportError:
        return {
            "environment": "local",
            "message": "Running in local environment"
        }

def get_local_ip() -> str:
    """Get the local IP address for LAN access"""
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

def main():
    """Main setup function"""
    print_step("Setting up Horror Story Video Generator")
    
    # Check environment
    env_info = check_environment()
    print(f"🔍 {env_info['message']}")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please check the errors above.")
        sys.exit(1)
    
    # Set up external access if in Colab
    if env_info["environment"] == "colab":
        ngrok_info = setup_ngrok()
        if not ngrok_info["success"]:
            print("⚠️ Failed to set up ngrok, but continuing with local access only.")
    else:
        # Show local IP for LAN access
        local_ip = get_local_ip()
        print(f"\n📡 Your app will be available at:")
        print(f"🖥️ Local URL: http://127.0.0.1:5000")
        print(f"📱 LAN URL: http://{local_ip}:5000 (accessible from devices on your network)")
    
    print("\n✅ Setup complete! You can now run the web app with: python web_app.py")

if __name__ == "__main__":
    try:
        main() 
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unhandled error during setup: {str(e)}")
        sys.exit(1) 