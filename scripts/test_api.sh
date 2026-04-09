#!/bin/bash
# API Testing Script - Tests all MongoDB-backed endpoints

set -e

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo "=========================================="
echo "3D Reconstruction API Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" -d "$data")
    elif [ "$method" = "PATCH" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PATCH "$API_URL$endpoint" \
            -H "Content-Type: application/json" -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. Health Check"
echo "----------------------------------------"
test_endpoint "Health endpoint" "GET" "/health"
echo ""

echo "2. Job Management"
echo "----------------------------------------"
test_endpoint "Create job" "POST" "/api/jobs/" \
    '{"user_id": "test_user_2", "name": "API Test Job", "description": "Testing all endpoints"}'

# Extract job_id from last response
JOB_ID=$(echo "$response" | head -n-1 | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")

if [ -n "$JOB_ID" ]; then
    echo -e "${YELLOW}Created job: $JOB_ID${NC}"
    
    test_endpoint "List jobs" "GET" "/api/jobs/"
    test_endpoint "Get job by ID" "GET" "/api/jobs/$JOB_ID"
    test_endpoint "Update job" "PATCH" "/api/jobs/$JOB_ID" \
        '{"name": "Updated API Test Job"}'
    test_endpoint "Get job stats" "GET" "/api/jobs/$JOB_ID/stats"
else
    echo -e "${RED}Failed to create job, skipping dependent tests${NC}"
fi
echo ""

echo "3. Status Tracking"
echo "----------------------------------------"
if [ -n "$JOB_ID" ]; then
    test_endpoint "Get job status" "GET" "/api/status/$JOB_ID"
else
    echo -e "${YELLOW}Skipped (no job ID)${NC}"
fi
echo ""

echo "4. Upload"
echo "----------------------------------------"
if [ -n "$JOB_ID" ]; then
    # Create test file
    echo "Test image data" > /tmp/test_upload.jpg
    
    echo -n "Testing file upload... "
    upload_response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/upload/" \
        -F "job_id=$JOB_ID" \
        -F "files=@/tmp/test_upload.jpg")
    
    upload_code=$(echo "$upload_response" | tail -n1)
    
    if [ "$upload_code" -ge 200 ] && [ "$upload_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $upload_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $upload_code)"
        FAILED=$((FAILED + 1))
    fi
    
    test_endpoint "Get upload info" "GET" "/api/upload/$JOB_ID"
else
    echo -e "${YELLOW}Skipped (no job ID)${NC}"
fi
echo ""

echo "5. Download (should fail - job not completed)"
echo "----------------------------------------"
if [ -n "$JOB_ID" ]; then
    echo -n "Testing download endpoint... "
    download_response=$(curl -s -w "\n%{http_code}" "$API_URL/api/download/$JOB_ID")
    download_code=$(echo "$download_response" | tail -n1)
    
    # Should return 400 since job not completed
    if [ "$download_code" = "400" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (correctly rejected - HTTP $download_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC} (expected 400, got $download_code)"
        FAILED=$((FAILED + 1))
    fi
    
    test_endpoint "Get results" "GET" "/api/download/$JOB_ID/results"
else
    echo -e "${YELLOW}Skipped (no job ID)${NC}"
fi
echo ""

echo "6. Frontend Proxy"
echo "----------------------------------------"
test_endpoint "Frontend proxy" "GET" "/api/jobs/" "" "$FRONTEND_URL"
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
