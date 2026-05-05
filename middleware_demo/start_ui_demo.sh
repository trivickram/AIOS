#!/bin/bash

# AIOS Middleware Demo - UI Launcher
# This script starts all required services for the web UI demo

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AIOS_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║            AIOS Middleware Demo - Web UI Launcher                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check virtual environment
if [ ! -d "$AIOS_ROOT/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Activate virtual environment
source "$AIOS_ROOT/venv/bin/activate"

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=15
    local attempt=0

    echo -e "${BLUE}⏳ Waiting for $name...${NC}"

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
    echo -e "${RED}❌ $name failed to start${NC}"
    return 1
}

echo "Starting services..."
echo ""

# Start Flask servers if not running
if ! check_port 5001 || ! check_port 5002; then
    echo -e "${BLUE}🚀 Starting Flask servers (ports 5001, 5002)...${NC}"
    cd "$SCRIPT_DIR"
    nohup python flask_servers.py > flask_servers.log 2>&1 &
    wait_for_service "http://localhost:5001/health" "Source Server"
    wait_for_service "http://localhost:5002/health" "Destination Server"
else
    echo -e "${GREEN}✅ Flask servers already running${NC}"
fi

# Start UI server if not running
if ! check_port 3000; then
    echo -e "${BLUE}🚀 Starting UI server (port 3000)...${NC}"
    cd "$SCRIPT_DIR"
    nohup python ui_server.py > ui_server.log 2>&1 &
    wait_for_service "http://localhost:3000/health" "UI Server"
else
    echo -e "${GREEN}✅ UI server already running${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                        ✅ ALL SERVICES RUNNING                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🌐 Open your browser and navigate to:${NC}"
echo ""
echo -e "   ${YELLOW}👉 http://localhost:3000${NC}"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║  Services:                                                               ║"
echo "║  • Web UI:              http://localhost:3000                            ║"
echo "║  • Source Server:       http://localhost:5001                            ║"
echo "║  • Destination Server:  http://localhost:5002                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}📝 Log files:${NC}"
echo "   • Flask Servers: $SCRIPT_DIR/flask_servers.log"
echo "   • UI Server:     $SCRIPT_DIR/ui_server.log"
echo ""
echo -e "${YELLOW}🛑 To stop all services, run:${NC}"
echo "   pkill -f flask_servers.py"
echo "   pkill -f ui_server.py"
echo ""
