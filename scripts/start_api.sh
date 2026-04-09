#!/bin/bash
# Start the new REST API

set -e

echo "=== Starting 3D Reconstruction REST API ==="
echo ""

# Check if MongoDB is running
if ! sudo docker ps | grep -q 3d-recon-mongodb; then
    echo "Starting MongoDB..."
    sudo docker-compose -f docker/docker-compose.yml up -d mongodb
    sleep 3
fi

echo "✓ MongoDB is running"
echo ""

# Activate virtual environment
cd backend
source venv/bin/activate

# Start API
echo "Starting API server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
