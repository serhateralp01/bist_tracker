#!/bin/bash

# BIST Portfolio Tracker - Startup Script
# This script starts both backend and frontend servers

echo "🚀 Starting BIST Portfolio Tracker..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Node modules not found. Please run setup.sh first."
    exit 1
fi

echo "📡 Starting backend server..."
# Start backend in background
source venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "⚛️ Starting frontend server..."
# Start frontend in background
cd frontend && npm start &
FRONTEND_PID=$!

echo "✅ Both servers started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped."
    exit 0
}

# Set trap to catch Ctrl+C
trap cleanup INT

# Wait for both processes
wait 