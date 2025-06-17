#!/bin/bash
# Start script for RAG UI with proper environment configuration

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UI_DIR="$PROJECT_ROOT/src/ui"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting RAG Document Chat UI${NC}"

# Check if UI directory exists
if [ ! -d "$UI_DIR" ]; then
    echo -e "${RED}❌ UI directory not found: $UI_DIR${NC}"
    exit 1
fi

# Navigate to UI directory
cd "$UI_DIR"

# Check for package.json
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in UI directory${NC}"
    exit 1
fi

# Environment configuration
ENVIRONMENT="${1:-development}"
echo -e "${YELLOW}🔧 Environment: $ENVIRONMENT${NC}"

# Set environment variables
export NODE_ENV="$ENVIRONMENT"
export REACT_APP_ENV="$ENVIRONMENT"

# Load environment file if it exists
ENV_FILE=".env.$ENVIRONMENT"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}📁 Loading environment from $ENV_FILE${NC}"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}⚠️ Environment file $ENV_FILE not found, using defaults${NC}"
fi

# Check if .env.local exists and load it
if [ -f ".env.local" ]; then
    echo -e "${GREEN}📁 Loading local environment from .env.local${NC}"
    set -a
    source ".env.local"
    set +a
fi

# Validate required environment variables
if [ -z "$REACT_APP_API_BASE_URL" ]; then
    echo -e "${YELLOW}⚠️ REACT_APP_API_BASE_URL not set, using default${NC}"
    export REACT_APP_API_BASE_URL="http://localhost:8003"
fi

echo -e "${BLUE}🔗 API Base URL: $REACT_APP_API_BASE_URL${NC}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Start based on command
case "${2:-start}" in
    "install")
        echo -e "${YELLOW}📦 Installing dependencies...${NC}"
        npm install
        ;;
    "build")
        echo -e "${YELLOW}🏗️ Building application...${NC}"
        npm run build
        ;;
    "start"|*)
        echo -e "${GREEN}🚀 Starting development server...${NC}"
        echo -e "${BLUE}📋 Environment Variables:${NC}"
        echo -e "  NODE_ENV=$NODE_ENV"
        echo -e "  REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL"
        echo -e "  REACT_APP_DEBUG_MODE=${REACT_APP_DEBUG_MODE:-false}"
        echo ""
        echo -e "${GREEN}🌐 UI will be available at: http://localhost:3000${NC}"
        echo -e "${GREEN}🔗 API should be running at: $REACT_APP_API_BASE_URL${NC}"
        echo ""
        
        # Check if API is reachable
        if command -v curl >/dev/null 2>&1; then
            echo -e "${YELLOW}🔍 Checking API connectivity...${NC}"
            if curl -s "$REACT_APP_API_BASE_URL/status" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ API is reachable${NC}"
            else
                echo -e "${RED}❌ API is not reachable at $REACT_APP_API_BASE_URL${NC}"
                echo -e "${YELLOW}💡 Make sure the API server is running:${NC}"
                echo -e "   cd $PROJECT_ROOT && ./scripts/start.sh"
            fi
            echo ""
        fi
        
        npm start
        ;;
esac