@echo off
REM BIST Portfolio Tracker - Start Script (Windows)
REM v0.2.1 - Fixed multiprocessing issues

echo 🚀 BIST Portfolio Tracker v0.2.1
echo =================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo 📦 Activating virtual environment...
call venv\Scripts\activate

echo 🔧 Starting backend server...
start /B python run_backend.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo ✅ Backend server started
echo 📖 API Documentation: http://127.0.0.1:8000/docs

echo 🎨 Starting frontend server...
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing frontend dependencies...
    npm install
)

echo 🎉 Starting frontend development server...
npm start

echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend: http://127.0.0.1:8000
echo 📖 API Docs: http://127.0.0.1:8000/docs

pause 