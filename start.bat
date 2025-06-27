@echo off
REM BIST Portfolio Tracker - Windows Startup Script

echo 🚀 Starting BIST Portfolio Tracker...

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo ❌ Node modules not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo 📡 Starting backend server...
REM Start backend
start "Backend Server" cmd /k "venv\Scripts\activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

echo ⚛️ Starting frontend server...
REM Start frontend
start "Frontend Server" cmd /k "cd frontend && npm start"

echo ✅ Both servers started!
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause 