#!/bin/bash
# Complete Workflow Demo - End-to-End Test

set -e

echo "=========================================="
echo "3D Reconstruction Pipeline - Complete Demo"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${BLUE}This demo will:${NC}"
echo "1. Create a new reconstruction job"
echo "2. Upload test images"
echo "3. Start processing"
echo "4. Monitor progress"
echo "5. Download results"
echo ""

# Check if services are running
echo "Checking services..."
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend API is not running${NC}"
    echo "Please run: ./scripts/start_complete_system.sh"
    exit 1
fi
echo -e "${GREEN}✓ Backend API is running${NC}"

# Create test images
echo ""
echo "Step 1: Creating test images..."
TEST_DIR="/tmp/demo_images"
mkdir -p "$TEST_DIR"

# Create 3 simple test images using ImageMagick or Python
for i in 1 2 3; do
    if command -v convert &> /dev/null; then
        convert -size 640x480 xc:blue -pointsize 72 -fill white \
            -annotate +200+240 "Test Image $i" "$TEST_DIR/test_$i.jpg"
    else
        # Fallback: create with Python
        python3 << EOF
from PIL import Image, ImageDraw, ImageFont
import numpy as np

img = Image.new('RGB', (640, 480), color=(0, 0, 255))
draw = ImageDraw.Draw(img)
draw.text((200, 240), "Test Image $i", fill=(255, 255, 255))
img.save("$TEST_DIR/test_$i.jpg")
EOF
    fi
done

echo -e "${GREEN}✓ Created 3 test images${NC}"

# Step 2: Create job
echo ""
echo "Step 2: Creating reconstruction job..."
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/api/jobs/" \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "demo_user",
        "name": "Demo Reconstruction",
        "description": "Complete workflow demonstration"
    }')

JOB_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}✗ Failed to create job${NC}"
    echo "$CREATE_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Job created: $JOB_ID${NC}"

# Step 3: Upload images
echo ""
echo "Step 3: Uploading test images..."
UPLOAD_CMD="curl -s -X POST \"$API_URL/api/upload/\" -F \"job_id=$JOB_ID\""
for i in 1 2 3; do
    UPLOAD_CMD="$UPLOAD_CMD -F \"files=@$TEST_DIR/test_$i.jpg\""
done

UPLOAD_RESPONSE=$(eval $UPLOAD_CMD)
NUM_FILES=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['num_files'])" 2>/dev/null || echo "0")

if [ "$NUM_FILES" -eq "3" ]; then
    echo -e "${GREEN}✓ Uploaded 3 images${NC}"
else
    echo -e "${RED}✗ Upload failed${NC}"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

# Step 4: Start processing
echo ""
echo "Step 4: Starting processing..."
PROCESS_RESPONSE=$(curl -s -X POST "$API_URL/api/process/$JOB_ID/start")
PROCESS_STATUS=$(echo "$PROCESS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null || echo "error")

if [ "$PROCESS_STATUS" = "processing" ]; then
    echo -e "${GREEN}✓ Processing started${NC}"
else
    echo -e "${YELLOW}⚠ Processing status: $PROCESS_STATUS${NC}"
    echo "$PROCESS_RESPONSE"
fi

# Step 5: Monitor progress
echo ""
echo "Step 5: Monitoring progress..."
echo -e "${BLUE}(This may take a few minutes)${NC}"
echo ""

MAX_WAIT=300  # 5 minutes
WAIT_TIME=0
LAST_STAGE=""
LAST_PROGRESS=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "$API_URL/api/status/$JOB_ID")
    
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    STAGE=$(echo "$STATUS_RESPONSE" | python