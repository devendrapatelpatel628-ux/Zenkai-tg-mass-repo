#!/usr/bin/env python3
"""
Quick start script for TeleManager Backend
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")


def install_dependencies():
    print("📦 Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"
    ])
    print("✅ Dependencies installed")


def create_directories():
    Path("./sessions").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
    print("✅ Directories created")


def run_server():
    print("\n🚀 Starting server...\n")
    subprocess.call([sys.executable, "main.py"])


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              TeleManager Backend Setup                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    check_python_version()
    install_dependencies()
    create_directories()
    run_server()
