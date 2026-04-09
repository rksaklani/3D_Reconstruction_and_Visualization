#!/bin/bash
set -e

echo "Deploying 3D Reconstruction Pipeline to production..."

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Build containers
echo "Building containers..."
./scripts/deploy/build_all.sh

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker/docker-compose.yml down

# Start new containers
echo "Starting new containers..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Run database migrations (if any)
echo "Running database migrations..."
docker-compose -f docker/docker-compose.yml exec -T backend python -m alembic upgrade head || true

# Setup MinIO buckets
echo "Setting up MinIO buckets..."
docker-compose -f docker/docker-compose.yml exec -T backend python scripts/setup/setup_minio.py || true

echo "Deployment complete!"
echo "Services:"
echo "  - Frontend: http://localhost"
echo "  - Backend API: http://localhost:8000"
echo "  - MinIO Console: http://localhost:9001"
