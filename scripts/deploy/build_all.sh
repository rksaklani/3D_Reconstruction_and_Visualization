#!/bin/bash
set -e

echo "Building all Docker containers..."

# Build backend
echo "Building backend..."
docker build -t 3d-recon-backend:latest -f docker/backend.Dockerfile .

# Build frontend
echo "Building frontend..."
docker build -t 3d-recon-frontend:latest -f docker/frontend.Dockerfile .

# Build AI services
echo "Building AI services..."
docker build -t 3d-recon-ai:latest -f docker/ai.Dockerfile .

# Build reconstruction services
echo "Building reconstruction services..."
docker build -t 3d-recon-reconstruction:latest -f docker/reconstruction.Dockerfile .

echo "All containers built successfully!"
