#!/bin/bash
# Script to check what files would be tracked by git
# Helps identify large files before committing

echo "=========================================="
echo "Git Status Check"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "⚠️  Git repository not initialized"
    echo "Run: git init"
    exit 1
fi

echo "📊 Repository Statistics:"
echo ""

# Count tracked files
TRACKED=$(git ls-files | wc -l)
echo "Tracked files: $TRACKED"

# Show largest tracked files
echo ""
echo "📦 Largest tracked files:"
git ls-files | xargs -I{} du -h {} 2>/dev/null | sort -hr | head -10

# Check for large untracked files
echo ""
echo "⚠️  Large untracked files (>1MB):"
find . -type f -size +1M \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/reconstruction/*-src/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/venv/*" \
    -not -path "*/storage/*" \
    -not -path "*/ai/models/*" \
    2>/dev/null | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  $size  $file"
done

# Check for files that should be ignored
echo ""
echo "🔍 Checking for files that should be in .gitignore:"

# Check for __pycache__
PYCACHE=$(find . -type d -name "__pycache__" | wc -l)
if [ $PYCACHE -gt 0 ]; then
    echo "  ⚠️  Found $PYCACHE __pycache__ directories"
fi

# Check for node_modules
NODEMOD=$(find . -type d -name "node_modules" -not -path "*/node_modules/*" | wc -l)
if [ $NODEMOD -gt 0 ]; then
    echo "  ⚠️  Found $NODEMOD node_modules directories"
fi

# Check for .pyc files
PYCFILES=$(find . -name "*.pyc" | wc -l)
if [ $PYCFILES -gt 0 ]; then
    echo "  ⚠️  Found $PYCFILES .pyc files"
fi

# Check for reconstruction source directories
if [ -d "reconstruction/colmap-src" ]; then
    echo "  ⚠️  Found reconstruction/colmap-src (should be gitignored)"
fi
if [ -d "reconstruction/ceres-src" ]; then
    echo "  ⚠️  Found reconstruction/ceres-src (should be gitignored)"
fi
if [ -d "reconstruction/abseil-src" ]; then
    echo "  ⚠️  Found reconstruction/abseil-src (should be gitignored)"
fi
if [ -d "reconstruction/gaussian-splatting-src" ]; then
    echo "  ⚠️  Found reconstruction/gaussian-splatting-src (should be gitignored)"
fi

echo ""
echo "=========================================="
echo "✅ Check complete"
echo "=========================================="
echo ""
echo "To see what would be committed:"
echo "  git status"
echo ""
echo "To see file sizes that would be committed:"
echo "  git ls-files | xargs du -h | sort -hr | head -20"
