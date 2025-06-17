#!/bin/bash
# Start script for RAG Modern UI (Next.js) with proper environment configuration

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting RAG Document Chat Modern UI (Next.js)${NC}"

# Navigate to project root
cd "$PROJECT_ROOT"

# Check for package.json
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in project root${NC}"
    exit 1
fi

# Check for ui.tsx (main UI component)
if [ ! -f "ui.tsx" ]; then
    echo -e "${RED}❌ ui.tsx not found in project root${NC}"
    exit 1
fi

# Environment configuration
ENVIRONMENT="${1:-development}"
echo -e "${YELLOW}🔧 Environment: $ENVIRONMENT${NC}"

# Set environment variables
export NODE_ENV="$ENVIRONMENT"

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

# API Base URL (uses proxy in development)
API_URL="http://localhost:8000"
echo -e "${BLUE}🔗 Backend API URL: $API_URL${NC}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Check if required shadcn/ui components are installed
if [ ! -d "components/ui" ]; then
    echo -e "${YELLOW}⚠️ shadcn/ui components directory not found${NC}"
    echo -e "${YELLOW}💡 UI components should be in components/ui/${NC}"
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
        echo -e "${GREEN}🚀 Starting Next.js development server...${NC}"
        echo -e "${BLUE}📋 Configuration:${NC}"
        echo -e "  NODE_ENV=$NODE_ENV"
        echo -e "  Next.js Port: 3004"
        echo -e "  External Access: Enabled (0.0.0.0)"
        echo -e "  API Proxy: /api/proxy/* -> $API_URL"
        echo ""
        echo -e "${GREEN}🌐 UI will be available at:${NC}"
        echo -e "  Local: http://localhost:3004"
        echo -e "  Network: http://0.0.0.0:3004"
        echo -e "  External: http://YOUR_SERVER_IP:3004"
        echo ""
        
        # Check if API is reachable
        if command -v curl >/dev/null 2>&1; then
            echo -e "${YELLOW}🔍 Checking backend API connectivity...${NC}"
            if curl -s "$API_URL/status" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Backend API is reachable at $API_URL${NC}"
            else
                echo -e "${RED}❌ Backend API is not reachable at $API_URL${NC}"
                echo -e "${YELLOW}💡 Start the backend API server:${NC}"
                echo -e "   python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000"
            fi
            echo ""
        fi
        
        # Check for PostCSS config (needed for Tailwind)
        if [ ! -f "postcss.config.js" ]; then
            echo -e "${YELLOW}⚠️ postcss.config.js not found, CSS might not work properly${NC}"
        fi
        
        # Check for Tailwind config
        if [ ! -f "tailwind.config.js" ]; then
            echo -e "${YELLOW}⚠️ tailwind.config.js not found, styling might not work${NC}"
        fi
        
        npm run dev
        ;;
esac