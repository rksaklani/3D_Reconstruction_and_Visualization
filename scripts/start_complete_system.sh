#!/bin/bash
# Complete System Startup Script
# Starts all services: MongoDB, MinIO, Backend API, Frontend

set -e

echo "=========================================="
echo "3D Reconstruction Pipeline - System Startup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "backend/api/main.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}✗ Timeout${NC}"
    return 1
}

echo "1. Starting Docker Services"
echo "----------------------------------------"

# Check if Docker is running
if ! sudo docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker first"
    exit 1
fi

# Start MongoDB
echo -n "Starting MongoDB... "
if sudo docker ps | grep -q "3d-recon-mongodb"; then
    echo -e "${YELLOW}Already running${NC}"
else
    sudo docker-compose -f docker/docker-compose.yml up -d mongodb
    echo -e "${GREEN}✓ Started${NC}"
fi

# Start MinIO
echo -n "Starting MinIO... "
if sudo docker ps | grep -q "3d-recon-minio"; then
    echo -e "${YELLOW}Already running${NC}"
else
    sudo docker-compose -f docker/docker-compose.yml up -d minio
    echo -e "${GREEN}✓ Started${NC}"
fi

# Wait for services
wait_for_service "http://localhost:9000/minio/health/live" "MinIO"
sleep 2  # Give MongoDB a moment

echo ""
echo "2. Starting Backend API"
echo "----------------------------------------"

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}Backend already running on port 8000${NC}"
else
    # Check if virtual environment exists
    if [ ! -d "backend/venv" ]; then
        echo -e "${RED}✗ Virtual environment not found${NC}"
        echo "Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Start backend in background
    echo "Starting backend API..."
    cd backend
    source venv/bin/activate
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Save PID
    mkdir -p logs
    echo $BACKEND_PID > logs/backend.pid
    
    # Wait for backend
    wait_for_service "http://localhost:8000/health" "Backend API"
fi

echo ""
echo "3. Starting Frontend"
echo "----------------------------------------"

# Check if frontend is already running
if check_port 3000; then
    echo -e "${YELLOW}Frontend already running on port 3000${NC}"
else
    # Check if node_modules exists
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${RED}✗ Node modules not found${NC}"
        echo "Run: cd frontend && npm install"
        exit 1
    fi
    
    # Start frontend in background
    echo "Starting frontend..."
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Save PID
    echo $FRONTEND_PID > logs/frontend.pid
    
    # Wait for frontend
    sleep 5
    if check_port 3000; then
        echo -e "${GREEN}✓ Frontend started${NC}"
    else
        echo -e "${RED}✗ Frontend failed to start${NC}"
        echo "Check logs/frontend.log for details"
    fi
fi

echo ""
echo "=========================================="
echo "System Status"
echo "=========================================="

# Check all services
echo ""
echo "Docker Services:"
sudo docker ps --filter "name=3d-recon" --format "  {{.Names}}: {{.Status}}"

echo ""
echo "Application Services:"

if check_port 8000; then
    echo -e "  Backend API: ${GREEN}✓ Running${NC} (http://localhost:8000)"
else
    echo -e "  Backend API: ${RED}✗ Not running${NC}"
fi

if check_port 3000; then
    echo -e "  Frontend: ${GREEN}✓ Running${NC} (http://localhost:3000)"
else
    echo -e "  Frontend: ${RED}✗ Not running${NC}"
fi

echo ""
echo "=========================================="
echo "Quick Links"
echo "=========================================="
echo "  Frontend:        http://localhost:3000"
echo "  Backend API:     http://localhost:8000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  MinIO Console:   http://localhost:9001"
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop all services:"
echo "  ./scripts/stop_complete_system.sh"
echo ""
echo -e "${GREEN}✓ System startup complete!${NC}"
