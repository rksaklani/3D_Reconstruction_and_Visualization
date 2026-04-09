#!/bin/bash
# Start all services

set -e

echo "=== Starting 3D Reconstruction Pipeline ==="
echo ""

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "Error: Backend virtual environment not found"
    echo "Please run: ./scripts/setup_backend.sh"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not installed"
    echo "Please run: ./scripts/setup_frontend.sh"
    exit 1
fi

echo "Starting backend server..."
cd backend
source venv/bin/activate
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo "Backend started (PID: $BACKEND_PID)"
echo ""

sleep 3

echo "Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Frontend started (PID: $FRONTEND_PID)"
echo ""
echo "=== Services Running ==="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
