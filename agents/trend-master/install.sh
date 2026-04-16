#!/bin/bash

echo "🚀 Starting installation for Trend-Master..."

# 1. Check for Node.js
if ! command -v node &> /dev/null
then
    echo "❌ Node.js could not be found. Please install Node.js first."
    exit
fi

# 2. Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install --silent

# 3. Check for Python3 and install Whisper
if ! command -v python3 &> /dev/null
then
    echo "⚠️ Python3 could not be found. Some features might not work."
else
    echo "🐍 Python3 is available. Installing Whisper..."
    python3 -m pip install -U openai-whisper --quiet
fi

# 4. Check for ffmpeg (Required for audio processing)
if ! command -v ffmpeg &> /dev/null
then
    echo "⚠️ ffmpeg not found. Please install it (e.g., sudo apt install ffmpeg) for audio features."
else
    echo "🎵 ffmpeg is available."
fi

# 5. Create necessary directories
echo "📂 Creating data and reports directories..."
mkdir -p data reports

# 5. Check for configuration files
if [ ! -f .env ]; then
    echo "⚠️ .env file missing. Please create it using .env.example as a template."
fi

if [ ! -f credentials.json ]; then
    echo "⚠️ credentials.json missing. Google Sheet integration will not work."
fi

echo "✅ Installation complete!"
echo "To start the online worker, run: node scripts/online_worker.js"
