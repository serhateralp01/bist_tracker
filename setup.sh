#!/bin/bash

# BIST Portfolio Tracker - Setup Script for macOS/Linux
# This script sets up the entire project with one command

echo "🏗️ Setting up BIST Portfolio Tracker..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    echo "📥 Download from: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "📥 Download from: https://nodejs.org/"
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

cd ..

# Make scripts executable
chmod +x start.sh
chmod +x setup.sh

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the application:"
echo "  Option 1: Run ./start.sh"
echo "  Option 2: Manual start:"
echo "    Terminal 1: source venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo "    Terminal 2: cd frontend && npm start"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs" 