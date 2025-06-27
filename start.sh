#!/bin/bash

# BIST Portfolio Tracker - Start Script (macOS/Linux)
# v0.2.1 - Fixed multiprocessing issues

echo "🚀 BIST Portfolio Tracker v0.2.1"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Start backend in background with improved method
echo -e "${BLUE}🔧 Starting backend server...${NC}"
python run_backend.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Backend server started successfully (PID: $BACKEND_PID)${NC}"
    echo -e "${BLUE}📖 API Documentation: http://127.0.0.1:8000/docs${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Please check the logs.${NC}"
    exit 1
fi

# Start frontend
echo -e "${BLUE}🎨 Starting frontend server...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend development server
npm start &
FRONTEND_PID=$!

echo -e "${GREEN}🎉 Both servers are starting!${NC}"
echo -e "${BLUE}🌐 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}🔧 Backend: http://127.0.0.1:8000${NC}"
echo -e "${BLUE}📖 API Docs: http://127.0.0.1:8000/docs${NC}"
echo ""
echo -e "${YELLOW}📋 Process IDs:${NC}"
echo -e "   Backend: $BACKEND_PID"
echo -e "   Frontend: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}⚠️  To stop both servers, run: kill $BACKEND_PID $FRONTEND_PID${NC}"
echo -e "${YELLOW}   Or use Ctrl+C to stop frontend, then manually stop backend${NC}"

# Wait for frontend (this will keep the script running)
wait $FRONTEND_PID 