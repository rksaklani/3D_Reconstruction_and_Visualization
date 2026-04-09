#!/bin/bash
set -e

echo "Starting development environment..."

# Start services with development overrides
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d

echo "Development environment started!"
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Adminer (DB): http://localhost:8080"
echo "  - Flower (Celery): http://localhost:5555"
echo ""
echo "To view logs: docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml logs -f"
echo "To stop: docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down"
