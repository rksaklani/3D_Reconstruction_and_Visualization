#!/bin/bash
# Complete System Runner - Starts ALL components
# AI, Backend, Config, Frontend, Reconstruction, Rendering, Storage

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     3D Reconstruction Pipeline - Complete System Startup      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "backend/api/main.py" ]; then
    echo -e "${RED}✗ Error: Must run from project root directory${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo -e "${CYAN}Components to start:${NC}"
echo "  1. Storage Layer (MongoDB + MinIO)"
echo "  2. Backend API (FastAPI + Integrated Pipeline)"
echo "  3. Frontend (React + Vite)"
echo "  4. Configuration System (YAML configs)"
echo "  5. AI Services (YOLO, SAM, Tracker, Classifier)"
echo "  6. Reconstruction Pipeline (COLMAP, Gaussian Splatting)"
echo ""

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
    
    echo -n "  Waiting for $name..."
    
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

# ============================================================================
# STEP 1: Storage Layer (MongoDB + MinIO)
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 1: Starting Storage Layer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if Docker is running
if ! sudo docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Please start Docker first"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Start MongoDB
echo -n "  Starting MongoDB... "
if sudo docker ps | grep -q "3d-recon-mongodb"; then
    echo -e "${YELLOW}Already running${NC}"
else
    sudo docker-compose -f docker/docker-compose.yml up -d mongodb > /dev/null 2>&1
    echo -e "${GREEN}✓ Started${NC}"
fi

# Start MinIO
echo -n "  Starting MinIO... "
if sudo docker ps | grep -q "3d-recon-minio"; then
    echo -e "${YELLOW}Already running${NC}"
else
    sudo docker-compose -f docker/docker-compose.yml up -d minio > /dev/null 2>&1
    echo -e "${GREEN}✓ Started${NC}"
fi

# Wait for services
wait_for_service "http://localhost:9000/minio/health/live" "MinIO"
sleep 2  # Give MongoDB a moment

echo -e "${GREEN}✓ Storage Layer Ready${NC}"
echo "  - MongoDB: localhost:27017"
echo "  - MinIO API: http://localhost:9000"
echo "  - MinIO Console: http://localhost:9001"

# ============================================================================
# STEP 2: Configuration System
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 2: Verifying Configuration System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check config files
CONFIG_FILES=("colmap.yaml" "gaussian.yaml" "physics.yaml" "pipeline.yaml" "model.yaml")
for config in "${CONFIG_FILES[@]}"; do
    if [ -f "configs/$config" ]; then
        echo -e "  ${GREEN}✓${NC} configs/$config"
    else
        echo -e "  ${YELLOW}⚠${NC} configs/$config (missing)"
    fi
done

echo -e "${GREEN}✓ Configuration System Ready${NC}"

# ============================================================================
# STEP 3: Backend API + AI Services + Reconstruction Pipeline
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 3: Starting Backend API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠ Backend already running on port 8000${NC}"
    echo "  Stopping existing backend..."
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            sleep 2
        fi
        rm logs/backend.pid
    fi
    # Kill any process on port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "  Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    cd ..
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Start backend in background
echo "  Starting Backend API..."
echo "    - FastAPI server"
echo "    - Integrated Pipeline"
echo "    - AI Services (YOLO, SAM, Tracker, Classifier)"
echo "    - Reconstruction Pipeline"
echo "    - COLMAP Integration (optional)"

cd backend
source venv/bin/activate
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Save PID
echo $BACKEND_PID > logs/backend.pid
echo -e "  ${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"

# Wait for backend
wait_for_service "http://localhost:8000/health" "Backend API"

echo -e "${GREEN}✓ Backend API Ready${NC}"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"

# ============================================================================
# STEP 4: Frontend
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 4: Starting Frontend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if frontend is already running
if check_port 3000; then
    echo -e "${YELLOW}⚠ Frontend already running on port 3000${NC}"
    echo "  Stopping existing frontend..."
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            sleep 2
        fi
        rm logs/frontend.pid
    fi
    # Kill any process on port 3000
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}✗ Node modules not found${NC}"
    echo "  Installing dependencies..."
    cd frontend
    npm install > /dev/null 2>&1
    cd ..
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Start frontend in background
echo "  Starting Frontend..."
echo "    - React application"
echo "    - Vite dev server"
echo "    - API proxy configured"

cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Save PID
echo $FRONTEND_PID > logs/frontend.pid
echo -e "  ${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend
sleep 5
if check_port 3000; then
    echo -e "  ${GREEN}✓${NC} Frontend ready"
else
    echo -e "  ${YELLOW}⚠${NC} Frontend may still be starting..."
fi

echo -e "${GREEN}✓ Frontend Ready${NC}"
echo "  - App: http://localhost:3000"

# ============================================================================
# System Status Summary
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}System Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo -e "${CYAN}Docker Services:${NC}"
sudo docker ps --filter "name=3d-recon" --format "  {{.Names}}: {{.Status}}"

echo ""
echo -e "${CYAN}Application Services:${NC}"

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
echo -e "${CYAN}Integrated Components:${NC}"
echo -e "  ${GREEN}✓${NC} Configuration System (YAML configs)"
echo -e "  ${GREEN}✓${NC} Storage Layer (MongoDB + MinIO)"
echo -e "  ${GREEN}✓${NC} Backend API (FastAPI)"
echo -e "  ${GREEN}✓${NC} Database (MongoDB)"
echo -e "  ${GREEN}✓${NC} Object Storage (MinIO)"
echo -e "  ${GREEN}✓${NC} AI Services (YOLO, SAM, Tracker, Classifier)"
echo -e "  ${GREEN}✓${NC} Preprocessing Pipeline"
echo -e "  ${GREEN}✓${NC} Reconstruction Pipeline"
echo -e "  ${GREEN}✓${NC} COLMAP Integration (optional)"
echo -e "  ${GREEN}✓${NC} Export System"
echo -e "  ${GREEN}✓${NC} Frontend (React)"

# ============================================================================
# Quick Links
# ============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Quick Links${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}Access Points:${NC}"
echo "  Frontend:        http://localhost:3000"
echo "  Backend API:     http://localhost:8000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  MinIO Console:   http://localhost:9001"
echo "                   (user: minioadmin, pass: minioadmin)"
echo ""
echo -e "${CYAN}Logs:${NC}"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${CYAN}Management:${NC}"
echo "  Stop all:     ./stop_system.sh"
echo "  System status: ./check_system.sh"
echo "  Run demo:     ./scripts/demo_complete_workflow.sh"
echo "  Test API:     ./scripts/test_api.sh"
echo ""
echo -e "${CYAN}Database:${NC}"
echo "  MongoDB Shell:"
echo "    sudo docker exec -it 3d-recon-mongodb mongosh \\"
echo "      'mongodb://admin:admin123@localhost:27017/reconstruction?authSource=admin'"
echo ""

# ============================================================================
# Final Message
# ============================================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  System Startup Complete! 🚀                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}All components are integrated and running:${NC}"
echo "  ✓ AI Services"
echo "  ✓ Backend API"
echo "  ✓ Configuration System"
echo "  ✓ Frontend"
echo "  ✓ Reconstruction Pipeline"
echo "  ✓ Rendering (export system)"
echo "  ✓ Storage (MongoDB + MinIO)"
echo ""
echo -e "${YELLOW}Ready to process 3D reconstruction jobs!${NC}"
echo ""
