#!/bin/bash

echo "╔══════════════════════════════════════════════════════════╗"
echo "║              🚀 TeleManager Backend Setup                 ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Check Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python is not installed. Please install Python 3.8+"
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

echo "✅ Found Python: $($PYTHON --version)"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Create directories
mkdir -p sessions data

# Run server
echo ""
echo "🚀 Starting server..."
echo ""
$PYTHON main.py
