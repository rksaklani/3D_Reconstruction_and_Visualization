#!/bin/bash
# Script to initialize git and push to GitHub repository

set -e  # Exit on error

REPO_URL="git@github.com:rksaklani/3D_Reconstruction_and_Visualization.git"

echo "=========================================="
echo "Git Setup and Push to GitHub"
echo "=========================================="
echo ""

# Check if git is already initialized
if [ -d ".git" ]; then
    echo "✓ Git repository already initialized"
else
    echo "Initializing git repository..."
    git init
    echo "✓ Git initialized"
fi

echo ""
echo "Checking .gitignore..."
if [ -f ".gitignore" ]; then
    echo "✓ .gitignore exists"
else
    echo "⚠️  Warning: .gitignore not found!"
    exit 1
fi

echo ""
echo "Adding files to git..."
git add .

echo ""
echo "Creating initial commit..."
git commit -m "Initial commit: 3D Reconstruction and Visualization Pipeline

- Complete monorepo structure (backend, ai, reconstruction, rendering, frontend)
- Comprehensive spec files (design, requirements, tasks)
- Configuration files (pipeline, model, minio)
- Setup scripts for dependencies
- Documentation (README, STRUCTURE, GIT_SETUP)
- Proper .gitignore (excludes 6GB+ reconstruction sources)

Note: Large dependencies (COLMAP, Ceres, Gaussian Splatting) must be installed locally using scripts/setup/install_reconstruction_deps.sh"

echo ""
echo "Setting default branch to main..."
git branch -M main

echo ""
echo "Adding remote repository..."
if git remote | grep -q "origin"; then
    echo "Remote 'origin' already exists, updating URL..."
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

echo ""
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "✅ Successfully pushed to GitHub!"
echo "=========================================="
echo ""
echo "Repository: $REPO_URL"
echo ""
echo "Next steps for other developers:"
echo "1. Clone the repository"
echo "2. Run: scripts/setup/install_reconstruction_deps.sh"
echo "3. Run: cd backend && pip install -r requirements.txt"
echo "4. Run: cd frontend && npm install"
