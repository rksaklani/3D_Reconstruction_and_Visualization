#!/bin/bash
# Stop all services

echo "Stopping 3D Reconstruction Pipeline..."

# Stop backend
if [ -f "logs/backend.pid" ]; then
    PID=$(cat logs/backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $PID)..."
        kill $PID
        rm logs/backend.pid
    fi
fi

# Stop frontend
if [ -f "logs/frontend.pid" ]; then
    PID=$(cat logs/frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $PID)..."
        kill $PID
        rm logs/frontend.pid
    fi
fi

# Stop Docker services
echo "Stopping Docker services..."
sudo docker-compose -f docker/docker-compose.yml stop

echo "✓ All services stopped"
