#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🚀 Starting RAG Document Chat System"
echo "===================================="

# Check if setup has been run
if [ ! -d "rag_env" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

if [ ! -f ".env" ]; then
    print_error "Environment file not found. Please copy .env.example to .env and configure it"
    exit 1
fi

# Activate virtual environment
source rag_env/bin/activate
print_status "Virtual environment activated"

# Load environment variables
source .env
print_status "Environment variables loaded"

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    print_error "Please set your OPENAI_API_KEY in the .env file"
    exit 1
fi

# Start ChromaDB if not running
if ! curl -s http://localhost:8002/api/v1/heartbeat > /dev/null 2>&1; then
    print_warning "Starting ChromaDB..."
    docker-compose up -d chromadb
    
    # Wait for ChromaDB to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8002/api/v1/heartbeat > /dev/null 2>&1; then
            print_status "ChromaDB is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "ChromaDB failed to start"
            exit 1
        fi
        sleep 2
    done
else
    print_status "ChromaDB is already running"
fi

# Ask user which interface to start
echo ""
echo "Which interface would you like to start?"
echo "1) Web Interface (Streamlit) - Recommended"
echo "2) API Server (FastAPI)"
echo "3) Both"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        print_status "Starting Web Interface..."
        echo "Access the application at: http://localhost:8501"
        streamlit run app.py
        ;;
    2)
        print_status "Starting API Server..."
        echo "API documentation at: http://localhost:8001/docs"
        python app.py api
        ;;
    3)
        print_status "Starting both interfaces..."
        echo "Web Interface: http://localhost:8501"
        echo "API Server: http://localhost:8001"
        echo ""
        
        # Start API in background
        python app.py api &
        API_PID=$!
        
        # Start Streamlit in foreground
        streamlit run app.py &
        STREAMLIT_PID=$!
        
        # Wait for both processes
        wait $API_PID $STREAMLIT_PID
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac
