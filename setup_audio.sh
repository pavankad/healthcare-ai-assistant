#!/bin/bash
# Setup script for audio transcription dependencies

echo "🎤 Setting up Audio Transcription Dependencies"
echo "============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

echo "✅ pip3 found"

# Install system dependencies for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS - installing system dependencies"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "🍺 Installing PortAudio for PyAudio..."
    brew install portaudio
    
    echo "🔧 Installing FFmpeg for audio processing..."
    brew install ffmpeg
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux - installing system dependencies"
    
    # Check if apt is available (Debian/Ubuntu)
    if command -v apt &> /dev/null; then
        echo "📦 Installing dependencies with apt..."
        sudo apt update
        sudo apt install -y portaudio19-dev python3-pyaudio ffmpeg
    
    # Check if yum is available (RHEL/CentOS)
    elif command -v yum &> /dev/null; then
        echo "📦 Installing dependencies with yum..."
        sudo yum install -y portaudio-devel python3-pyaudio ffmpeg
    
    # Check if pacman is available (Arch Linux)
    elif command -v pacman &> /dev/null; then
        echo "📦 Installing dependencies with pacman..."
        sudo pacman -S portaudio python-pyaudio ffmpeg
    
    else
        echo "⚠️  Unknown Linux distribution. Please install portaudio and ffmpeg manually."
    fi
    
else
    echo "⚠️  Unknown operating system. Please install portaudio and ffmpeg manually."
fi

echo ""
echo "🐍 Installing Python dependencies..."

# Install Python packages
pip3 install -r requirements_audio.txt

echo ""
echo "🧪 Testing installation..."

# Test if imports work
python3 -c "
import pyaudio
import whisper
import numpy as np
print('✅ All Python packages imported successfully')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Audio transcription setup completed successfully!"
    echo ""
    echo "📋 Usage Examples:"
    echo "  1. Basic audio transcription:"
    echo "     python3 audio_transcriber.py"
    echo ""
    echo "  2. Transcribe an existing audio file:"
    echo "     python3 audio_transcriber.py --file path/to/audio.wav"
    echo ""
    echo "  3. Clinical voice recording:"
    echo "     python3 clinical_audio_example.py 1 'Dr. Smith'"
    echo ""
    echo "  4. Different Whisper model sizes:"
    echo "     python3 audio_transcriber.py --model small"
    echo "     python3 audio_transcriber.py --model large"
    echo ""
    echo "📝 Available Whisper models (by size and accuracy):"
    echo "   - tiny: Fastest, least accurate"
    echo "   - base: Good balance (default)"
    echo "   - small: Better accuracy"
    echo "   - medium: High accuracy"
    echo "   - large: Best accuracy, slowest"
    echo ""
else
    echo ""
    echo "❌ Installation test failed. Please check the errors above."
    exit 1
fi
