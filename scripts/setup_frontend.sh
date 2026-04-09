#!/bin/bash
# Frontend setup script

set -e

echo "=== 3D Reconstruction Pipeline - Frontend Setup ==="
echo ""

# Check Node.js version
echo "Checking Node.js version..."
node --version
npm --version

# Install dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install

echo ""
echo "=== Frontend Setup Complete ==="
echo ""
echo "To start the frontend dev server:"
echo "  cd frontend && npm run dev"
echo ""
echo "Frontend will be available at: http://localhost:3000"
echo ""
