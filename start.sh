#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🚀 Starting RAG Document Chat System v2"
echo "========================================"

# Check if setup has been run
if [ ! -d "rag_env" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

if [ ! -f ".env" ]; then
    print_error "Environment file not found. Please copy sample.env.txt to .env and configure it"
    exit 1
fi

# Check if we have the main app files
if [ ! -f "streamlit_app.py" ] && [ ! -f "app_refactored.py" ]; then
    print_error "Main application files not found. Please ensure you're in the correct directory"
    exit 1
fi

# Activate virtual environment
source rag_env/bin/activate
print_status "Virtual environment activated"

# Load environment variables
set -a  # automatically export all variables
source .env
set +a
print_status "Environment variables loaded"

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "KEYHERE" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    print_error "Please set your OPENAI_API_KEY in the .env file"
    print_info "Edit .env and replace KEYHERE with your actual OpenAI API key"
    exit 1
fi

# Start ChromaDB if not running
print_info "Checking ChromaDB status..."
if ! curl -s http://localhost:8002/api/v2/heartbeat > /dev/null 2>&1; then
    print_warning "Starting ChromaDB..."
    
    # Clean up any hanging processes
    if [ -f "cleanup_chroma_ports.sh" ]; then
        ./cleanup_chroma_ports.sh > /dev/null 2>&1 || true
    fi
    
    # Start ChromaDB
    docker-compose up -d chromadb
    
    # Wait for ChromaDB to be ready
    print_info "Waiting for ChromaDB to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8002/api/v2/heartbeat > /dev/null 2>&1; then
            print_status "ChromaDB is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "ChromaDB failed to start after 60 seconds"
            print_info "Check logs with: docker-compose logs chromadb"
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
else
    print_status "ChromaDB is already running"
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep ":$port " > /dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop process on port
stop_port_process() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ ! -z "$pid" ]; then
        print_warning "Stopping existing process on port $port (PID: $pid)"
        kill $pid 2>/dev/null || true
        sleep 2
    fi
}

# Ask user which interface to start
echo ""
echo "Which interface would you like to start?"
echo "1) Web Interface (Streamlit) - Recommended for interactive use"
echo "2) API Server (FastAPI) - For programmatic access"
echo "3) Both interfaces"
echo "4) Background mode (both interfaces as daemons)"
echo ""
read -p "Enter choice (1-4, default 1): " choice
choice=${choice:-1}

case $choice in
    1)
        print_status "Starting Web Interface..."
        
        # Check if port 8501 is in use
        if check_port 8501; then
            print_warning "Port 8501 is already in use"
            read -p "Stop existing process and restart? (y/N): " restart
            if [[ $restart =~ ^[Yy]$ ]]; then
                stop_port_process 8501
            else
                print_info "Existing Streamlit might already be running at http://localhost:8501"
                exit 0
            fi
        fi
        
        print_info "Access the web interface at:"
        print_info "  Local: http://localhost:8501"
        print_info "  Network: http://$(hostname -I | awk '{print $1}'):8501"
        echo ""
        
        # Download NLTK data if needed
        python3 -c "import nltk; nltk.download('punkt', quiet=True)" > /dev/null 2>&1 || true
        
        streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
        ;;
    2)
        print_status "Starting API Server..."
        
        # Check if port 8000 is in use
        if check_port 8000; then
            print_warning "Port 8000 is already in use"
            read -p "Stop existing process and restart? (y/N): " restart
            if [[ $restart =~ ^[Yy]$ ]]; then
                stop_port_process 8000
            else
                print_info "Existing API server might already be running at http://localhost:8000"
                exit 0
            fi
        fi
        
        print_info "Access the API at:"
        print_info "  Local: http://localhost:8000"
        print_info "  Docs: http://localhost:8000/docs"
        print_info "  Network: http://$(hostname -I | awk '{print $1}'):8000"
        echo ""
        
        # Download NLTK data if needed
        python3 -c "import nltk; nltk.download('punkt', quiet=True)" > /dev/null 2>&1 || true
        
        python3 app_refactored.py
        ;;
    3)
        print_status "Starting both interfaces..."
        
        # Check ports
        ports_in_use=""
        if check_port 8501; then
            ports_in_use="$ports_in_use 8501"
        fi
        if check_port 8000; then
            ports_in_use="$ports_in_use 8000"
        fi
        
        if [ ! -z "$ports_in_use" ]; then
            print_warning "Ports$ports_in_use already in use"
            read -p "Stop existing processes and restart? (y/N): " restart
            if [[ $restart =~ ^[Yy]$ ]]; then
                for port in $ports_in_use; do
                    stop_port_process $port
                done
            else
                print_info "Some services might already be running"
            fi
        fi
        
        print_info "Access the applications at:"
        print_info "  Web Interface: http://localhost:8501"
        print_info "  API Server: http://localhost:8000"
        print_info "  API Docs: http://localhost:8000/docs"
        echo ""
        
        # Download NLTK data if needed
        python3 -c "import nltk; nltk.download('punkt', quiet=True)" > /dev/null 2>&1 || true
        
        # Start API in background
        python3 app_refactored.py &
        API_PID=$!
        echo "API Server started with PID: $API_PID"
        
        # Give API time to start
        sleep 3
        
        # Start Streamlit in foreground
        echo "Starting Streamlit..."
        streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 &
        STREAMLIT_PID=$!
        echo "Streamlit started with PID: $STREAMLIT_PID"
        
        # Setup cleanup on exit
        cleanup() {
            echo ""
            print_info "Shutting down services..."
            kill $API_PID 2>/dev/null || true
            kill $STREAMLIT_PID 2>/dev/null || true
            print_status "Services stopped"
        }
        trap cleanup EXIT
        
        # Wait for both processes
        wait $API_PID $STREAMLIT_PID
        ;;
    4)
        print_status "Starting background services..."
        
        # Download NLTK data if needed
        python3 -c "import nltk; nltk.download('punkt', quiet=True)" > /dev/null 2>&1 || true
        
        # Start API server in background
        nohup python3 app_refactored.py > api_server.log 2>&1 &
        API_PID=$!
        echo $API_PID > api_server.pid
        print_status "API Server started (PID: $API_PID, log: api_server.log)"
        
        # Give API time to start
        sleep 3
        
        # Start Streamlit in background
        nohup streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 > streamlit.log 2>&1 &
        STREAMLIT_PID=$!
        echo $STREAMLIT_PID > streamlit.pid
        print_status "Streamlit started (PID: $STREAMLIT_PID, log: streamlit.log)"
        
        echo ""
        print_info "Services running in background:"
        print_info "  Web Interface: http://localhost:8501"
        print_info "  API Server: http://localhost:8000"
        print_info "  API Docs: http://localhost:8000/docs"
        echo ""
        print_info "To stop services:"
        print_info "  kill \$(cat api_server.pid streamlit.pid)"
        print_info "  rm -f api_server.pid streamlit.pid *.log"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac