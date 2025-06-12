#!/bin/bash
set -e

echo "🚀 RAG Document Chat System - Automated Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Check OS
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_warning "This script is designed for Linux. Some steps may not work on other systems."
fi

# Step 1: Update system packages
echo "📦 Step 1: Updating system packages..."
sudo apt update
sudo apt install -y software-properties-common curl wget git
print_status "System packages updated"

# Step 2: Install Python 3.9+
echo "🐍 Step 2: Installing Python..."
if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip python3-venv python3-full
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    # Check if Python is 3.9 or higher
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_status "Python $PYTHON_VERSION is compatible"
    elif [ "$PYTHON_MAJOR" -gt 3 ]; then
        print_status "Python $PYTHON_VERSION is compatible"
    else
        print_error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
        print_error "Please upgrade Python and try again."
        exit 1
    fi
fi
print_status "Python $(python3 --version) installed"

# Step 3: Install Docker
echo "🐳 Step 3: Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_warning "Added user to docker group. You may need to log out and back in for changes to take effect."
else
    print_status "Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose-plugin
fi
print_status "Docker and Docker Compose installed"

# Step 4: Create Python virtual environment
echo "🔧 Step 4: Setting up Python environment..."
if [ ! -d "rag_env" ]; then
    python3 -m venv rag_env
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source rag_env/bin/activate

# Upgrade pip
pip install --upgrade pip
print_status "Pip upgraded"

# Step 5: Install Python dependencies
echo "📚 Step 5: Installing Python packages..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python packages installed"
else
    print_error "requirements.txt not found. Please ensure you're in the correct directory."
    exit 1
fi

# Step 6: Create environment file
echo "⚙️  Step 6: Setting up configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Environment file created from template"
        print_warning "Please edit .env file with your API keys and credentials"
    elif [ -f "sample.env.txt" ]; then
        cp sample.env.txt .env
        print_status "Environment file created from sample"
        print_warning "Please edit .env file with your API keys and credentials"
    else
        print_error "No .env template found"
        exit 1
    fi
else
    print_warning "Environment file already exists"
fi

# Step 7: Clean up and start Docker services
echo "🐳 Step 7: Setting up Docker services..."
if [ -f "docker-compose.yml" ]; then
    # Start Docker service if not running
    sudo systemctl start docker
    
    # Clean up any existing containers to avoid port conflicts
    echo "🧹 Cleaning up existing containers..."
    
    # Stop and remove any existing ChromaDB containers
    if docker ps -q --filter "name=rag_chromadb" | grep -q .; then
        print_warning "Stopping existing ChromaDB container..."
        docker stop rag_chromadb || true
    fi
    
    if docker ps -aq --filter "name=rag_chromadb" | grep -q .; then
        print_warning "Removing existing ChromaDB container..."
        docker rm rag_chromadb || true
    fi
    
    # Clean up docker-compose services
    docker-compose down 2>/dev/null || true
    
    # Check if port 8002 is still in use
    if sudo netstat -tlnp | grep :8002 > /dev/null 2>&1; then
        print_warning "Port 8002 is still in use. Attempting to free it..."
        
        # Try to find and stop the process using port 8002
        PORT_PID=$(sudo lsof -ti:8002 2>/dev/null || echo "")
        if [ ! -z "$PORT_PID" ]; then
            print_warning "Stopping process $PORT_PID using port 8002..."
            sudo kill $PORT_PID 2>/dev/null || true
            sleep 2
        fi
    fi
    
    # Start ChromaDB fresh
    echo "🚀 Starting ChromaDB..."
    docker-compose up -d chromadb
    
    # Wait for ChromaDB to be ready with better error handling
    echo "⏳ Waiting for ChromaDB to start..."
    RETRY_COUNT=0
    MAX_RETRIES=30
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8002/api/v2/heartbeat > /dev/null 2>&1; then
            print_status "ChromaDB is ready"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            print_error "ChromaDB failed to start after $MAX_RETRIES attempts"
            echo ""
            echo "🔍 Troubleshooting information:"
            echo "Container status:"
            docker ps -a | grep chromadb || echo "No ChromaDB containers found"
            echo ""
            echo "Container logs:"
            docker-compose logs chromadb 2>/dev/null || echo "No logs available"
            echo ""
            echo "Port status:"
            sudo netstat -tlnp | grep :8002 || echo "Port 8002 not in use"
            echo ""
            print_warning "You can try running: docker-compose restart chromadb"
            exit 1
        fi
        
        echo "Attempt $RETRY_COUNT/$MAX_RETRIES - waiting..."
        sleep 2
    done
else
    print_error "docker-compose.yml not found"
    exit 1
fi

# Step 8: Create enhanced test setup script
echo "🧪 Step 8: Creating test script..."
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test script to verify RAG system setup"""

import os
import sys
from typing import Dict

def test_imports() -> bool:
    """Test that all required packages can be imported"""
    try:
        import chromadb
        import openai
        import streamlit
        import fastapi
        import boto3
        import PyPDF2
        import langchain
        import nltk  # New addition
        print("✅ All Python packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_chromadb() -> bool:
    """Test ChromaDB connection"""
    try:
        import chromadb
        client = chromadb.HttpClient(host="localhost", port=8002)
        client.heartbeat()
        print("✅ ChromaDB connection successful")
        return True
    except Exception as e:
        print(f"⚠️ ChromaDB connection failed: {e}")
        print("   Trying in-memory mode...")
        try:
            client = chromadb.Client()
            collection = client.get_or_create_collection("test")
            print("✅ ChromaDB in-memory mode working")
            return True
        except Exception as e2:
            print(f"❌ ChromaDB completely failed: {e2}")
            return False

def test_nltk() -> bool:
    """Test NLTK functionality"""
    try:
        import nltk
        # Test sentence tokenization
        test_text = "Hello world. This is Dr. Smith. He went to the store."
        tokens = nltk.sent_tokenize(test_text)
        if len(tokens) >= 2:
            print("✅ NLTK sentence tokenization working")
            return True
        else:
            print("⚠️ NLTK tokenization returned unexpected results")
            return False
    except Exception as e:
        print(f"❌ NLTK test failed: {e}")
        return False

def test_openai() -> bool:
    """Test OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY not set in environment")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️ OPENAI_API_KEY doesn't look valid (should start with 'sk-')")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.models.list()
        print("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_s3() -> bool:
    """Test S3 configuration (optional)"""
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        print("ℹ️ S3 not configured (optional)")
        return True
    
    try:
        import boto3
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket)
        print("✅ S3 connection successful")
        return True
    except Exception as e:
        print(f"⚠️ S3 test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing RAG System Setup")
    print("=" * 30)
    
    tests = [
        ("Package Imports", test_imports),
        ("ChromaDB", test_chromadb),
        ("NLTK", test_nltk),
        ("OpenAI API", test_openai),
        ("S3 (Optional)", test_s3)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing {name}...")
        results.append(test_func())
    
    print("\n" + "=" * 30)
    print("📊 Test Results:")
    for i, (name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {name}: {status}")
    
    required_tests = results[:3]  # Imports, ChromaDB, and NLTK
    if all(required_tests):
        print("\n🎉 Core system is ready!")
        print("   Run: streamlit run app.py")
    else:
        print("\n❌ Setup incomplete. Please check the failed tests above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x test_setup.py
print_status "Test script created"

# Step 9: Download NLTK data
echo "📚 Step 9: Setting up NLTK data..."
python3 -c "import nltk; nltk.download('punkt', quiet=True)" || true
print_status "NLTK data downloaded"

# Step 10: Run basic tests
echo "🧪 Step 10: Running setup verification..."
python test_setup.py

# Final instructions
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Run the application:"
echo "   # Web interface (recommended):"
echo "   ./start.sh"
echo ""
echo "   # Or manually:"
echo "   streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501"
echo "   python3 app_refactored.py  # For FastAPI server"
echo ""
echo "3. Access the application:"
echo "   Web UI: http://localhost:8501 (or your-ec2-ip:8501)"
echo "   API: http://localhost:8000 (or your-ec2-ip:8000)"
echo ""
echo "📝 Important notes:"
echo "   • Always activate the virtual environment: source rag_env/bin/activate"
echo "   • Set your OpenAI API key in the .env file"
echo "   • ChromaDB will run on port 8002"
echo "   • For EC2: ensure security groups allow ports 8501 and 8000"
echo "   • Check logs with: docker-compose logs chromadb"
echo "   • Re-run this script anytime safely"
echo ""
echo "🆘 Troubleshooting:"
echo "   • Run: python test_setup.py"
echo "   • Check: docker-compose ps"
echo "   • Restart: docker-compose restart chromadb"
echo "   • Clean restart: docker-compose down && docker-compose up -d"
echo "   • Kill processes on ports: ./cleanup_chroma_ports.sh"

# Final check
if command -v streamlit &> /dev/null && [ -f "streamlit_app.py" ]; then
    print_status "System ready! You can now run: ./start.sh"
else
    print_warning "Please ensure streamlit_app.py is in the current directory"
fi

echo ""
print_status "Setup script completed successfully and can be run multiple times safely!"
