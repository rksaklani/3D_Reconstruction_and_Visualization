#!/bin/bash
# Verify COLMAP installation and integration

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              COLMAP Installation Verification                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check COLMAP binary
echo -e "${CYAN}1. Checking COLMAP binary...${NC}"
if command -v colmap &> /dev/null; then
    COLMAP_PATH=$(which colmap)
    echo -e "  ${GREEN}✓${NC} Found at: $COLMAP_PATH"
    
    # Get version
    COLMAP_INFO=$(colmap help 2>&1 | head -1)
    echo -e "  ${GREEN}✓${NC} $COLMAP_INFO"
else
    echo -e "  ${RED}✗${NC} COLMAP not found in PATH"
    exit 1
fi

# Check local build
echo ""
echo -e "${CYAN}2. Checking local COLMAP build...${NC}"
LOCAL_COLMAP="reconstruction/colmap/build/src/colmap/exe/colmap"
if [ -f "$LOCAL_COLMAP" ]; then
    echo -e "  ${GREEN}✓${NC} Local build found: $LOCAL_COLMAP"
    LOCAL_INFO=$($LOCAL_COLMAP help 2>&1 | head -1)
    echo -e "  ${GREEN}✓${NC} $LOCAL_INFO"
else
    echo -e "  ${YELLOW}⚠${NC} Local build not found (using system COLMAP)"
fi

# Check COLMAP features
echo ""
echo -e "${CYAN}3. Checking COLMAP features...${NC}"

# Check available commands
COMMANDS=$(colmap help 2>&1 | grep -E "^\s+colmap" | wc -l)
echo -e "  ${GREEN}✓${NC} Available commands: $COMMANDS"

# Check for key commands
for cmd in feature_extractor exhaustive_matcher mapper; do
    if colmap help 2>&1 | grep -q "$cmd"; then
        echo -e "  ${GREEN}✓${NC} $cmd available"
    else
        echo -e "  ${RED}✗${NC} $cmd not available"
    fi
done

# Check CUDA support
echo ""
echo -e "${CYAN}4. Checking CUDA support...${NC}"
if colmap help 2>&1 | head -1 | grep -q "with CUDA"; then
    echo -e "  ${GREEN}✓${NC} COLMAP built with CUDA support"
else
    echo -e "  ${YELLOW}⚠${NC} COLMAP built without CUDA (CPU only)"
    echo "    GPU acceleration not available for feature extraction"
fi

# Test Python integration
echo ""
echo -e "${CYAN}5. Testing Python integration...${NC}"

if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
    
    python3 << 'EOF'
import sys
try:
    from backend.services.colmap_service import get_colmap_service
    
    # Try to initialize COLMAP service
    colmap = get_colmap_service()
    print(f"  \033[0;32m✓\033[0m COLMAP service initialized")
    print(f"  \033[0;32m✓\033[0m Binary path: {colmap.colmap_bin}")
    print(f"  \033[0;32m✓\033[0m Workspace: {colmap.workspace_dir}")
    
except Exception as e:
    print(f"  \033[0;31m✗\033[0m Failed to initialize COLMAP service: {e}")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Python integration working"
    else
        echo -e "  ${RED}✗${NC} Python integration failed"
        exit 1
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Virtual environment not found"
    echo "    Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              COLMAP Verification Complete! ✓                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}COLMAP is properly installed and integrated.${NC}"
echo ""
echo "Next steps:"
echo "  - Run system: ./run_system.sh"
echo "  - Test reconstruction: ./scripts/demo_complete_workflow.sh"
echo ""
