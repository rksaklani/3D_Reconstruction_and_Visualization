#!/bin/bash
# Stop all system components

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        3D Reconstruction Pipeline - System Shutdown            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Stop backend
echo "Stopping Backend API..."
if [ -f "logs/backend.pid" ]; then
    PID=$(cat logs/backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "  ${GREEN}✓${NC} Backend stopped (PID: $PID)"
        rm logs/backend.pid
    else
        echo -e "  ${YELLOW}⚠${NC} Backend not running"
        rm logs/backend.pid
    fi
else
    echo -e "  ${YELLOW}⚠${NC} No PID file found"
fi

# Kill any remaining process on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Cleaned up port 8000"
fi

# Stop frontend
echo "Stopping Frontend..."
if [ -f "logs/frontend.pid" ]; then
    PID=$(cat logs/frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "  ${GREEN}✓${NC} Frontend stopped (PID: $PID)"
        rm logs/frontend.pid
    else
        echo -e "  ${YELLOW}⚠${NC} Frontend not running"
        rm logs/frontend.pid
    fi
else
    echo -e "  ${YELLOW}⚠${NC} No PID file found"
fi

# Kill any remaining process on port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Cleaned up port 3000"
fi

# Stop Docker services
echo "Stopping Docker services..."
sudo docker-compose -f docker/docker-compose.yml stop > /dev/null 2>&1
echo -e "  ${GREEN}✓${NC} MongoDB stopped"
echo -e "  ${GREEN}✓${NC} MinIO stopped"

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
echo "To start again: ./run_system.sh"
