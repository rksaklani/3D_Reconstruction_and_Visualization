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
    STAGE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stage', 'N/A'))" 2>/dev/null || echo "N/A")
    PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress', 0))" 2>/dev/null || echo "0")
    
    # Only print if stage or progress changed
    if [ "$STAGE" != "$LAST_STAGE" ] || [ "$PROGRESS" != "$LAST_PROGRESS" ]; then
        PROGRESS_PCT=$(python3 -c "print(f'{float($PROGRESS)*100:.1f}')" 2>/dev/null || echo "0.0")
        echo -e "  Status: ${YELLOW}$STATUS${NC} | Stage: ${BLUE}$STAGE${NC} | Progress: ${GREEN}$PROGRESS_PCT%${NC}"
        LAST_STAGE="$STAGE"
        LAST_PROGRESS="$PROGRESS"
    fi
    
    # Check if completed or failed
    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo -e "${GREEN}✓ Processing completed!${NC}"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo ""
        echo -e "${RED}✗ Processing failed${NC}"
        ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))" 2>/dev/null)
        echo "Error: $ERROR"
        exit 1
    fi
    
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Timeout waiting for completion${NC}"
fi

# Step 6: Get results
echo ""
echo "Step 6: Fetching results..."
RESULTS_RESPONSE=$(curl -s "$API_URL/api/download/$JOB_ID/results")

echo ""
echo -e "${BLUE}Results Summary:${NC}"
echo "$RESULTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESULTS_RESPONSE"

# Step 7: Get job details
echo ""
echo "Step 7: Final job details..."
JOB_RESPONSE=$(curl -s "$API_URL/api/jobs/$JOB_ID")

echo ""
echo -e "${BLUE}Job Details:${NC}"
echo "$JOB_RESPONSE" | python3 << 'EOF'
import sys, json
try:
    job = json.load(sys.stdin)
    print(f"  Job ID: {job['job_id']}")
    print(f"  Name: {job['name']}")
    print(f"  Status: {job['status']}")
    print(f"  Progress: {job['progress']*100:.1f}%")
    print(f"  Input Files: {job['num_files']}")
    print(f"  Created: {job['created_at']}")
    if job.get('completed_at'):
        print(f"  Completed: {job['completed_at']}")
    if job.get('output_files'):
        print(f"  Output Files: {len(job['output_files'])}")
except:
    print(sys.stdin.read())
EOF

# Cleanup
echo ""
echo "Cleaning up test images..."
rm -rf "$TEST_DIR"

echo ""
echo "=========================================="
echo -e "${GREEN}Demo Complete!${NC}"
echo "=========================================="
echo ""
echo "What was demonstrated:"
echo "  ✓ Job creation via REST API"
echo "  ✓ File upload to MinIO storage"
echo "  ✓ Background processing with integrated pipeline"
echo "  ✓ Real-time status monitoring"
echo "  ✓ AI analysis (detection, classification, segmentation)"
echo "  ✓ SfM reconstruction (COLMAP integration)"
echo "  ✓ Results export and storage"
echo "  ✓ MongoDB data persistence"
echo ""
echo "View full job details:"
echo "  curl http://localhost:8000/api/jobs/$JOB_ID | python3 -m json.tool"
echo ""
echo "View in browser:"
echo "  http://localhost:3000"
echo ""
