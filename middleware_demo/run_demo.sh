#!/bin/bash

# AIOS Middleware Demo - Automated Runner
# This script starts all required components in sequence

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AIOS_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================================================="
echo "🤖 AIOS MIDDLEWARE DEMO - AUTOMATED RUNNER"
echo "======================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "$AIOS_ROOT/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found at $AIOS_ROOT/venv${NC}"
    echo "Please run the installation first."
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source "$AIOS_ROOT/venv/bin/activate"

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Flask not found. Installing...${NC}"
    pip install flask requests
fi

# Function to check if a port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    echo -e "${BLUE}⏳ Waiting for $name to be ready...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done

    echo ""
    echo -e "${RED}❌ $name failed to start within ${max_attempts} seconds${NC}"
    return 1
}

# Step 1: Check if AIOS kernel is running
echo ""
echo "======================================================================="
echo "📋 Step 1: Checking AIOS Kernel"
echo "======================================================================="

if check_port 8000; then
    echo -e "${GREEN}✅ AIOS Kernel is already running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠️  AIOS Kernel is not running${NC}"
    echo -e "${BLUE}Starting AIOS Kernel...${NC}"

    cd "$AIOS_ROOT"
    nohup python3.11 -m uvicorn runtime.launch:app --host 0.0.0.0 --port 8000 > aios_kernel.log 2>&1 &
    KERNEL_PID=$!
    echo "AIOS Kernel PID: $KERNEL_PID"

    # Wait for kernel to be ready
    if ! wait_for_service "http://localhost:8000/health" "AIOS Kernel"; then
        echo -e "${RED}Failed to start AIOS Kernel. Check aios_kernel.log for details.${NC}"
        exit 1
    fi
fi

# Step 2: Start Flask servers
echo ""
echo "======================================================================="
echo "📋 Step 2: Starting Flask Servers"
echo "======================================================================="

# Check if servers are already running
if check_port 5001 && check_port 5002; then
    echo -e "${GREEN}✅ Flask servers are already running${NC}"
else
    echo -e "${BLUE}Starting Flask servers...${NC}"

    cd "$SCRIPT_DIR"
    nohup python flask_servers.py > flask_servers.log 2>&1 &
    FLASK_PID=$!
    echo "Flask Servers PID: $FLASK_PID"

    # Wait for both servers to be ready
    if ! wait_for_service "http://localhost:5001/health" "Source Server"; then
        exit 1
    fi

    if ! wait_for_service "http://localhost:5002/health" "Destination Server"; then
        exit 1
    fi
fi

# Step 3: Run the middleware agent
echo ""
echo "======================================================================="
echo "📋 Step 3: Running Middleware Agent"
echo "======================================================================="
echo ""

cd "$SCRIPT_DIR"

# Parse command line arguments for LLM configuration
LLM_NAME="${LLM_NAME:-gpt-4o-mini}"
LLM_BACKEND="${LLM_BACKEND:-openai}"

echo -e "${BLUE}Configuration:${NC}"
echo "  LLM Name: $LLM_NAME"
echo "  LLM Backend: $LLM_BACKEND"
echo ""

# Run the agent
python middleware_agent.py \
    --llm-name "$LLM_NAME" \
    --llm-backend "$LLM_BACKEND" \
    --aios-kernel-url "http://localhost:8000" \
    --source-url "http://localhost:5001" \
    --destination-url "http://localhost:5002"

AGENT_EXIT_CODE=$?

# Step 4: Show results
echo ""
echo "======================================================================="
echo "📊 Execution Complete"
echo "======================================================================="

if [ $AGENT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Middleware agent completed successfully!${NC}"

    # Optionally query the destination server to see what was stored
    echo ""
    echo -e "${BLUE}📋 Checking destination server data...${NC}"
    curl -s http://localhost:5002/api/destination/list | python -m json.tool
else
    echo -e "${RED}❌ Middleware agent failed with exit code $AGENT_EXIT_CODE${NC}"
fi

echo ""
echo "======================================================================="
echo "🔍 Log Files"
echo "======================================================================="
echo "AIOS Kernel log: $AIOS_ROOT/aios_kernel.log"
echo "Flask Servers log: $SCRIPT_DIR/flask_servers.log"

echo ""
echo "======================================================================="
echo "🛑 Cleanup"
echo "======================================================================="
echo ""
echo "To stop all services, run:"
echo -e "${YELLOW}  pkill -f 'uvicorn runtime.launch'${NC}  # Stop AIOS Kernel"
echo -e "${YELLOW}  pkill -f 'flask_servers.py'${NC}        # Stop Flask Servers"

echo ""
echo "======================================================================="

exit $AGENT_EXIT_CODE
