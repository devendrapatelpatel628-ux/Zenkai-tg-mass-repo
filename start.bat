@echo off
echo ╔══════════════════════════════════════════════════════════╗
echo ║              🚀 TeleManager Backend Setup                 ║
echo ╚══════════════════════════════════════════════════════════╝

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+
    pause
    exit /b 1
)

echo ✅ Found Python

REM Create virtual environment if not exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt -q

REM Create directories
if not exist "sessions" mkdir sessions
if not exist "data" mkdir data

REM Run server
echo.
echo 🚀 Starting server...
echo.
python main.py

pause
