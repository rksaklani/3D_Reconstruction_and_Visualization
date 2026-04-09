#!/bin/bash
# Verify the new project structure

echo "🔍 Verifying Project Structure..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

echo "📁 Checking main directories..."
check_dir "backend"
check_dir "ai"
check_dir "reconstruction"
check_dir "rendering"
check_dir "frontend"
check_dir "storage"
check_dir "configs"
check_dir "docker"
check_dir "scripts"
echo ""

echo "📁 Checking backend structure..."
check_dir "backend/api"
check_dir "backend/pipeline"
check_dir "backend/workers"
check_dir "backend/services"
check_file "backend/api/server.py"
check_file "backend/requirements.txt"
echo ""

echo "📁 Checking AI structure..."
check_dir "ai/detection"
check_dir "ai/segmentation"
check_dir "ai/tracking"
check_dir "ai/classification"
check_dir "ai/models"
echo ""

echo "📁 Checking reconstruction structure..."
check_dir "reconstruction/colmap-src"
check_dir "reconstruction/ceres-src"
check_dir "reconstruction/abseil-src"
check_dir "reconstruction/gaussian-splatting-src"
echo ""

echo "📁 Checking rendering structure..."
check_dir "rendering/splat-renderer"
check_dir "rendering/shaders"
check_dir "rendering/webgl-utils"
echo ""

echo "📁 Checking frontend structure..."
check_dir "frontend/src"
check_dir "frontend/public"
check_file "frontend/package.json"
echo ""

echo "📁 Checking storage structure..."
check_dir "storage/uploads"
check_dir "storage/processed"
check_dir "storage/models"
echo ""

echo "📁 Checking config files..."
check_file "configs/pipeline.yaml"
check_file "configs/model.yaml"
check_file "configs/minio.yaml"
echo ""

echo "📁 Checking documentation..."
check_file "README.md"
check_file ".gitignore"
check_file "STRUCTURE.md"
check_file "MIGRATION_SUMMARY.md"
echo ""

echo "📁 Checking spec files..."
check_file ".kiro/specs/3d-reconstruction-pipeline/design.md"
check_file ".kiro/specs/3d-reconstruction-pipeline/requirements.md"
check_file ".kiro/specs/3d-reconstruction-pipeline/tasks.md"
echo ""

echo "✨ Structure verification complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Update import paths in backend/api/server.py"
echo "  2. Test backend: cd backend && python -m api.server"
echo "  3. Test frontend: cd frontend && npm run dev"
echo "  4. Remove old gs_platform/ after verification"
echo "  5. Start implementing tasks from .kiro/specs/3d-reconstruction-pipeline/tasks.md"
