#!/bin/bash
# Backend setup script

set -e

echo "=== 3D Reconstruction Pipeline - Backend Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=== Backend Setup Complete ==="
echo ""
echo "To activate the virtual environment:"
echo "  cd backend && source venv/bin/activate"
echo ""
echo "To start the backend server:"
echo "  uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"
echo ""
