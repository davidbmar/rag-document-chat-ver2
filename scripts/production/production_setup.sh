#!/bin/bash

echo "🚀 RAG Document Chat - Production Setup"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "cli.py" ]; then
    echo "❌ Error: Please run this script from the rag-document-chat-ver2 directory"
    exit 1
fi

echo "1️⃣ Checking environment configuration..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️ No .env file found. Creating from sample..."
    cp sample.env.txt .env
    echo "📝 Please edit .env with your actual API keys:"
    echo "   - OPENAI_API_KEY: Your OpenAI API key"
    echo "   - AWS_ACCESS_KEY_ID: Your AWS access key (optional)"
    echo "   - AWS_SECRET_ACCESS_KEY: Your AWS secret key (optional)"
    echo "   - S3_BUCKET: Your S3 bucket name (optional)"
    echo ""
    echo "🔧 Run: nano .env"
    echo ""
    read -p "Press Enter after configuring .env file..."
fi

# Source environment variables
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

echo "2️⃣ Checking virtual environment..."

# Activate virtual environment
if [ -d "rag_env" ]; then
    echo "✅ Virtual environment found"
    source rag_env/bin/activate
else
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv rag_env
    source rag_env/bin/activate
    pip install -r requirements.txt
fi

echo "3️⃣ Checking dependencies..."

# Check if all required packages are installed
python3 -c "
import sys
required_packages = ['fastapi', 'uvicorn', 'streamlit', 'openai', 'chromadb', 'boto3', 'requests']
missing = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - MISSING')
        missing.append(package)

if missing:
    print(f'\\n⚠️ Missing packages: {missing}')
    print('Installing missing packages...')
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
"

echo "4️⃣ Checking Docker services..."

# Check if ChromaDB is running
if docker ps | grep -q chromadb; then
    echo "✅ ChromaDB container is running"
else
    echo "🐳 Starting ChromaDB with Docker Compose..."
    docker-compose up -d chromadb
    sleep 5
    
    # Wait for ChromaDB to be ready
    echo "⏳ Waiting for ChromaDB to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8002/api/v2/heartbeat > /dev/null 2>&1; then
            echo "✅ ChromaDB is ready"
            break
        fi
        echo "   Attempt $i/30..."
        sleep 2
    done
fi

echo "5️⃣ Testing configuration..."

# Test OpenAI connection
echo "🧪 Testing OpenAI API connection..."
python3 -c "
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print('❌ OPENAI_API_KEY not set')
    exit(1)

if not api_key.startswith('sk-'):
    print('❌ Invalid OpenAI API key format')
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    models = client.models.list()
    print('✅ OpenAI API connection successful')
except Exception as e:
    print(f'❌ OpenAI API error: {e}')
"

# Test ChromaDB connection
echo "🧪 Testing ChromaDB connection..."
python3 -c "
import requests
try:
    response = requests.get('http://localhost:8002/api/v2/heartbeat', timeout=5)
    if response.status_code == 200:
        print('✅ ChromaDB connection successful')
    else:
        print(f'❌ ChromaDB returned status {response.status_code}')
except Exception as e:
    print(f'❌ ChromaDB connection error: {e}')
"

# Test S3 connection (optional)
echo "🧪 Testing S3 connection (optional)..."
python3 -c "
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
s3_bucket = os.getenv('S3_BUCKET')

if aws_key and aws_secret and s3_bucket:
    try:
        s3 = boto3.client('s3',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        s3.head_bucket(Bucket=s3_bucket)
        print('✅ S3 connection successful')
    except (ClientError, NoCredentialsError) as e:
        print(f'⚠️ S3 connection failed: {e}')
        print('   (S3 is optional - system will work without it)')
else:
    print('ℹ️ S3 not configured (optional)')
"

echo "6️⃣ Starting production services..."

# Kill any existing API server
pkill -f "uvicorn.*app_refactored" 2>/dev/null || true

# Start API server in production mode using config
echo "🚀 Starting FastAPI server..."
nohup python3 app_refactored.py api > api_production.log 2>&1 &

# Wait for server to start
echo "⏳ Waiting for API server to start..."
sleep 5

# Get API URL from config
API_URL=$(python3 -c "from config import config; print(config.api_url)")

# Test API server
for i in {1..10}; do
    if curl -s $API_URL/ > /dev/null 2>&1; then
        echo "✅ API server is running on $API_URL"
        break
    fi
    echo "   Attempt $i/10..."
    sleep 2
done

echo "7️⃣ Production health check..."

# Test CLI
echo "🧪 Testing CLI..."
python3 cli.py status

echo ""
echo "🎉 Production setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Test with: python3 cli.py list"
echo "   2. Upload documents: python3 cli.py process upload <file>"
echo "   3. Search: python3 cli.py search '<query>'"
echo "   4. Ask questions: python3 cli.py ask '<question>'"
echo ""
echo "📊 Monitor logs:"
echo "   API Server: tail -f api_production.log"
echo "   ChromaDB: docker logs -f \$(docker ps -q --filter name=chromadb)"
echo ""
echo "🌐 API Documentation: $API_URL/docs"