#!/bin/bash
# Installation script for reconstruction dependencies
# This script installs COLMAP, Ceres Solver, Abseil, and Gaussian Splatting

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RECON_DIR="$PROJECT_ROOT/reconstruction"

echo "=========================================="
echo "Installing Reconstruction Dependencies"
echo "=========================================="
echo ""

cd "$RECON_DIR"

# Check if dependencies already exist
if [ -d "colmap-src" ] && [ -d "ceres-src" ] && [ -d "abseil-src" ] && [ -d "gaussian-splatting-src" ]; then
    echo "All dependencies already exist. Skipping installation."
    echo "To reinstall, remove the directories and run this script again."
    exit 0
fi

# Install Abseil (required by Ceres)
if [ ! -d "abseil-src" ]; then
    echo "Installing Abseil C++..."
    git clone https://github.com/abseil/abseil-cpp.git abseil-src
    cd abseil-src
    mkdir -p build && cd build
    cmake .. -DCMAKE_POSITION_INDEPENDENT_CODE=ON
    make -j$(nproc)
    sudo make install
    cd "$RECON_DIR"
    echo "✓ Abseil installed"
else
    echo "✓ Abseil already exists"
fi

# Install Ceres Solver
if [ ! -d "ceres-src" ]; then
    echo "Installing Ceres Solver..."
    git clone https://github.com/ceres-solver/ceres-solver.git ceres-src
    cd ceres-src
    mkdir -p build && cd build
    cmake ..
    make -j$(nproc)
    sudo make install
    cd "$RECON_DIR"
    echo "✓ Ceres Solver installed"
else
    echo "✓ Ceres Solver already exists"
fi

# Install COLMAP
if [ ! -d "colmap-src" ]; then
    echo "Installing COLMAP..."
    git clone https://github.com/colmap/colmap.git colmap-src
    cd colmap-src
    mkdir -p build && cd build
    cmake .. -DCMAKE_CUDA_ARCHITECTURES=native
    make -j$(nproc)
    sudo make install
    cd "$RECON_DIR"
    echo "✓ COLMAP installed"
else
    echo "✓ COLMAP already exists"
fi

# Install Gaussian Splatting
if [ ! -d "gaussian-splatting-src" ]; then
    echo "Installing Gaussian Splatting..."
    git clone https://github.com/graphdeco-inria/gaussian-splatting.git gaussian-splatting-src
    cd gaussian-splatting-src
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Install submodules
    pip install submodules/diff-gaussian-rasterization
    pip install submodules/simple-knn
    
    cd "$RECON_DIR"
    echo "✓ Gaussian Splatting installed"
else
    echo "✓ Gaussian Splatting already exists"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "All reconstruction dependencies have been installed."
echo "Total size: ~6GB"
echo ""
echo "Note: These directories are excluded from git."
echo "Each developer needs to run this script to install them locally."
