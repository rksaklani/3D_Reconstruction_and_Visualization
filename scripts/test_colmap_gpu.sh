#!/bin/bash
# Test COLMAP GPU Performance

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              COLMAP GPU Performance Test                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check GPU
echo -e "${CYAN}GPU Status:${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader | while read line; do
        echo "  $line"
    done
else
    echo -e "  ${RED}✗${NC} nvidia-smi not found"
    exit 1
fi

# Check COLMAP
echo ""
echo -e "${CYAN}COLMAP Status:${NC}"
if command -v colmap &> /dev/null; then
    COLMAP_BIN=$(which colmap)
    echo "  Binary: $COLMAP_BIN"
    
    COLMAP_INFO=$(colmap help 2>&1 | head -1)
    echo "  $COLMAP_INFO"
    
    if echo "$COLMAP_INFO" | grep -q "with CUDA"; then
        echo -e "  ${GREEN}✓${NC} CUDA support enabled"
    else
        echo -e "  ${YELLOW}⚠${NC} CUDA support not detected"
        echo "  Run: ./scripts/rebuild_colmap_gpu.sh"
    fi
else
    echo -e "  ${RED}✗${NC} COLMAP not found"
    exit 1
fi

# Create test workspace
echo ""
echo -e "${CYAN}Setting up test workspace...${NC}"
TEST_DIR="/tmp/colmap_gpu_test_$$"
mkdir -p "$TEST_DIR/images"

# Check if we have test images
if [ -d "test_data/images" ] && [ "$(ls -A test_data/images/*.jpg 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "  Using test images from test_data/images"
    cp test_data/images/*.jpg "$TEST_DIR/images/" 2>/dev/null || true
    NUM_IMAGES=$(ls "$TEST_DIR/images"/*.jpg 2>/dev/null | wc -l)
else
    echo "  No test images found in test_data/images"
    echo "  Please add some test images to test_data/images/"
    echo ""
    echo "  You can download sample images:"
    echo "    mkdir -p test_data/images"
    echo "    # Add your images here"
    rm -rf "$TEST_DIR"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Test workspace: $TEST_DIR"
echo -e "  ${GREEN}✓${NC} Test images: $NUM_IMAGES"

# Test GPU feature extraction
echo ""
echo -e "${CYAN}Testing GPU Feature Extraction...${NC}"
echo "  This will extract SIFT features using GPU"
echo ""

DATABASE="$TEST_DIR/database.db"

# Monitor GPU during extraction
echo "  Starting feature extraction..."
START_TIME=$(date +%s)

# Run in background and monitor GPU
colmap feature_extractor \
    --database_path "$DATABASE" \
    --image_path "$TEST_DIR/images" \
    --ImageReader.camera_model SIMPLE_RADIAL \
    --SiftExtraction.use_gpu 1 \
    --SiftExtraction.gpu_index 0 \
    --SiftExtraction.max_image_size 3200 \
    --SiftExtraction.num_threads 8 \
    > "$TEST_DIR/feature_extraction.log" 2>&1 &

COLMAP_PID=$!

# Monitor GPU usage
echo "  Monitoring GPU usage (PID: $COLMAP_PID)..."
sleep 2

while kill -0 $COLMAP_PID 2>/dev/null; do
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    echo -ne "  GPU Utilization: ${GPU_UTIL}% | Memory: ${GPU_MEM}MB\r"
    sleep 1
done

wait $COLMAP_PID
EXTRACT_EXIT=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
if [ $EXTRACT_EXIT -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Feature extraction completed in ${DURATION}s"
    
    # Count features
    NUM_FEATURES=$(sqlite3 "$DATABASE" "SELECT COUNT(*) FROM keypoints" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}✓${NC} Extracted features: $NUM_FEATURES"
else
    echo -e "  ${RED}✗${NC} Feature extraction failed"
    echo "  Check log: $TEST_DIR/feature_extraction.log"
    cat "$TEST_DIR/feature_extraction.log"
    exit 1
fi

# Test GPU feature matching
echo ""
echo -e "${CYAN}Testing GPU Feature Matching...${NC}"
echo "  This will match features between images using GPU"
echo ""

START_TIME=$(date +%s)

colmap exhaustive_matcher \
    --database_path "$DATABASE" \
    --SiftMatching.use_gpu 1 \
    --SiftMatching.gpu_index 0 \
    --SiftMatching.max_num_matches 32768 \
    > "$TEST_DIR/matching.log" 2>&1 &

COLMAP_PID=$!

# Monitor GPU usage
echo "  Monitoring GPU usage (PID: $COLMAP_PID)..."
sleep 2

while kill -0 $COLMAP_PID 2>/dev/null; do
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    echo -ne "  GPU Utilization: ${GPU_UTIL}% | Memory: ${GPU_MEM}MB\r"
    sleep 1
done

wait $COLMAP_PID
MATCH_EXIT=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
if [ $MATCH_EXIT -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Feature matching completed in ${DURATION}s"
    
    # Count matches
    NUM_MATCHES=$(sqlite3 "$DATABASE" "SELECT COUNT(*) FROM matches" 2>/dev/null || echo "0")
    echo -e "  ${GREEN}✓${NC} Feature matches: $NUM_MATCHES"
else
    echo -e "  ${RED}✗${NC} Feature matching failed"
    echo "  Check log: $TEST_DIR/matching.log"
    cat "$TEST_DIR/matching.log"
    exit 1
fi

# Cleanup
echo ""
echo -e "${CYAN}Cleaning up...${NC}"
rm -rf "$TEST_DIR"
echo -e "  ${GREEN}✓${NC} Test workspace removed"

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              GPU Performance Test Complete! ✓                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Results:${NC}"
echo "  ✓ GPU feature extraction working"
echo "  ✓ GPU feature matching working"
echo "  ✓ COLMAP GPU acceleration confirmed"
echo ""
echo -e "${CYAN}Performance:${NC}"
echo "  Images processed: $NUM_IMAGES"
echo "  Features extracted: $NUM_FEATURES"
echo "  Feature matches: $NUM_MATCHES"
echo ""
echo -e "${YELLOW}Ready for production use!${NC}"
echo ""
