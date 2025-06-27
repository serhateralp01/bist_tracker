@echo off
REM BIST Portfolio Tracker - Setup Script for Windows

echo 🏗️ Setting up BIST Portfolio Tracker...

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH.
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    echo ⚠️ Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH.
    echo 📥 Please install Node.js 16+ from: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed!

REM Create virtual environment
echo 🐍 Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)

cd ..

echo.
echo 🎉 Setup completed successfully!
echo.
echo To start the application:
echo   Option 1: Double-click start.bat
echo   Option 2: Manual start:
echo     Terminal 1: venv\Scripts\activate ^&^& uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
echo     Terminal 2: cd frontend ^&^& npm start
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
pause 