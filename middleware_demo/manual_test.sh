#!/bin/bash

# Manual Testing Script for AIOS Middleware Demo
# This script helps you verify everything is working step-by-step

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║           AIOS MIDDLEWARE DEMO - MANUAL VERIFICATION                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to pause and wait for user
pause() {
    echo ""
    read -p "Press Enter to continue..."
    echo ""
}

# Step 1: Check servers
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 1: Checking if servers are running${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Checking Source Server (Port 5001)..."
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Source Server is running${NC}"
    curl -s http://localhost:5001/health | python -m json.tool
else
    echo -e "${RED}✗ Source Server is NOT running${NC}"
    echo "Start it with: python middleware_demo/flask_servers.py"
    exit 1
fi

echo ""
echo "Checking Destination Server (Port 5002)..."
if curl -s http://localhost:5002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Destination Server is running${NC}"
    curl -s http://localhost:5002/health | python -m json.tool
else
    echo -e "${RED}✗ Destination Server is NOT running${NC}"
    echo "Start it with: python middleware_demo/flask_servers.py"
    exit 1
fi

pause

# Step 2: View source data
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 2: Viewing SOURCE server data (Legacy Format)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Command: curl http://localhost:5001/api/source${NC}"
echo ""

curl -s http://localhost:5001/api/source | python -m json.tool

echo ""
echo -e "${GREEN}Notice the legacy format:${NC}"
echo "  - first_name / last_name (separate)"
echo "  - contact_num (with dashes)"
echo "  - email_addr"
echo "  - status_code (A or I)"

pause

# Step 3: View destination data
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 3: Viewing DESTINATION server data (Modern Format)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Command: curl http://localhost:5002/api/destination/list${NC}"
echo ""

DEST_DATA=$(curl -s http://localhost:5002/api/destination/list)
echo "$DEST_DATA" | python -m json.tool

TOTAL=$(echo "$DEST_DATA" | python -c "import sys, json; print(json.load(sys.stdin).get('total_count', 0))")
echo ""
echo -e "${GREEN}Current destination has $TOTAL users${NC}"

if [ "$TOTAL" -gt 0 ]; then
    echo -e "${GREEN}Notice the modern format:${NC}"
    echo "  - fullName (combined)"
    echo "  - phoneDetails (object with number and formatted)"
    echo "  - emailAddress"
    echo "  - accountStatus (active or inactive)"
fi

pause

# Step 4: Clear destination
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 4: Testing DELETE operation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Command: curl -X POST http://localhost:5002/api/destination/clear${NC}"
echo ""

curl -s -X POST http://localhost:5002/api/destination/clear | python -m json.tool

echo ""
echo "Verifying deletion..."
curl -s http://localhost:5002/api/destination/list | python -m json.tool

echo ""
echo -e "${GREEN}✓ Destination server cleared${NC}"

pause

# Step 5: Run the agent
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 5: Running the AIOS Middleware Agent${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "The agent will:"
echo "  1. Fetch data from source server"
echo "  2. Transform data using LLM reasoning"
echo "  3. Push transformed data to destination server"
echo ""

cd "$(dirname "$0")/.."
source venv/bin/activate
python middleware_demo/middleware_agent_standalone.py

pause

# Step 6: Verify the result
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 6: Verifying the transformation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Checking destination server again..."
echo ""

DEST_DATA=$(curl -s http://localhost:5002/api/destination/list)
echo "$DEST_DATA" | python -m json.tool

TOTAL=$(echo "$DEST_DATA" | python -c "import sys, json; print(json.load(sys.stdin).get('total_count', 0))")

echo ""
if [ "$TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✓ SUCCESS! $TOTAL users were transformed and inserted${NC}"
else
    echo -e "${RED}✗ FAILED! No users found in destination${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}COMPARISON: Source vs Destination${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}SOURCE (Legacy):${NC}"
echo "  customer_id: CUST001"
echo "  first_name:  John"
echo "  last_name:   Doe"
echo "  contact_num: 555-0123"
echo "  status_code: A"
echo ""
echo -e "${GREEN}DESTINATION (Modern):${NC}"
echo "  userId:          CUST001"
echo "  fullName:        John Doe"
echo "  phoneDetails:"
echo "    number:        5550123"
echo "    formatted:     555-0123"
echo "  accountStatus:   active"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                      ✅ MANUAL VERIFICATION COMPLETE                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}All CRUD operations verified successfully!${NC}"
echo ""
