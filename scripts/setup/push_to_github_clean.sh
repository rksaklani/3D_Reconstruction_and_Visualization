#!/bin/bash
# Script to push clean repository to GitHub (without .kiro specs)

set -e  # Exit on error

REPO_URL="git@github.com:rksaklani/3D_Reconstruction_and_Visualization.git"

echo "=========================================="
echo "Clean Git Push to GitHub"
echo "=========================================="
echo ""

# Initialize git
echo "Initializing git repository..."
git init
echo "✓ Git initialized"

echo ""
echo "Adding files to git (excluding .kiro)..."
git add .

echo ""
echo "Creating clean commit..."
git commit -m "Initial commit: 3D Reconstruction and Visualization Pipeline

Complete monorepo structure:
- Backend API with FastAPI
- Frontend with React + Vite + Babylon.js
- AI scene understanding structure
- Rendering engine structure
- Configuration files (pipeline, model, minio)
- Setup scripts for dependencies
- Documentation

Note: Large dependencies (COLMAP, Ceres, Gaussian Splatting) must be installed locally using scripts/setup/install_reconstruction_deps.sh"

echo ""
echo "Setting default branch to main..."
git branch -M main

echo ""
echo "Adding remote repository..."
git remote add origin "$REPO_URL"

echo ""
echo "Force pushing to GitHub (this will overwrite the previous commit)..."
git push -u origin main --force

echo ""
echo "=========================================="
echo "✅ Successfully pushed clean version!"
echo "=========================================="
echo ""
echo "Repository: $REPO_URL"
echo ""
echo "Excluded from git:"
echo "  - .kiro/ (internal spec files)"
echo "  - reconstruction/*-src/ (6GB+ dependencies)"
echo "  - node_modules/"
echo "  - Python cache files"
