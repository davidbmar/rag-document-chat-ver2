#!/bin/bash

echo "🔧 Thorough Port 8002 Cleanup and ChromaDB Reset"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

echo "1️⃣ Diagnosing what's using port 8002..."
echo "----------------------------------------"

# Check what's using port 8002
echo "🔍 Processes using port 8002:"
sudo lsof -i :8002 || echo "No processes found with lsof"
sudo netstat -tlnp | grep :8002 || echo "No processes found with netstat"
sudo ss -tulpn | grep :8002 || echo "No processes found with ss"

echo ""
echo "2️⃣ Nuclear Docker cleanup..."
echo "----------------------------"

# Stop ALL containers (nuclear option)
print_warning "Stopping ALL Docker containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "No containers to stop"

# Remove ALL containers
print_warning "Removing ALL Docker containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove docker-compose services
print_warning "Removing docker-compose services..."
docker-compose down --remove-orphans 2>/dev/null || echo "No docker-compose services"

# Remove networks
print_warning "Removing Docker networks..."
docker network prune -f 2>/dev/null || echo "No networks to remove"

echo ""
echo "3️⃣ Kill any remaining processes on port 8002..."
echo "-----------------------------------------------"

# More aggressive process killing
PIDS=$(sudo lsof -ti :8002 2>/dev/null || echo "")
if [ ! -z "$PIDS" ]; then
    print_warning "Force killing processes: $PIDS"
    echo $PIDS | xargs -r sudo kill -9
    sleep 3
else
    print_status "No processes found using port 8002"
fi

# Double check
PIDS_AFTER=$(sudo lsof -ti :8002 2>/dev/null || echo "")
if [ ! -z "$PIDS_AFTER" ]; then
    print_error "Processes still running: $PIDS_AFTER"
    echo "Manual intervention needed"
    exit 1
fi

echo ""
echo "4️⃣ Verify port 8002 is free..."
echo "------------------------------"

if sudo netstat -tlnp | grep :8002 > /dev/null 2>&1; then
    print_error "Port 8002 is still in use!"
    sudo netstat -tlnp | grep :8002
    exit 1
else
    print_status "Port 8002 is now free"
fi

echo ""
echo "5️⃣ Clean Docker system..."
echo "------------------------"

# Clean up Docker system
docker system prune -f || echo "Docker system prune failed"

echo ""
echo "6️⃣ Start ChromaDB with fresh setup..."
echo "------------------------------------"

# Try starting ChromaDB
print_status "Starting ChromaDB..."
docker-compose up -d chromadb

# Wait a bit
sleep 5

echo ""
echo "7️⃣ Verify ChromaDB is working..."
echo "-------------------------------"

# Check if container is running
if docker ps | grep chromadb > /dev/null; then
    print_status "ChromaDB container is running"
    
    # Test the endpoint
    if curl -s http://localhost:8002/api/v1/heartbeat > /dev/null 2>&1; then
        print_status "ChromaDB is responding to API calls"
        echo "🎉 SUCCESS: ChromaDB is fully operational!"
    else
        print_warning "Container running but not responding to API calls"
        echo "Container logs:"
        docker-compose logs chromadb
    fi
else
    print_error "ChromaDB container is not running"
    echo "Docker status:"
    docker ps -a | grep chromadb || echo "No ChromaDB containers found"
    echo ""
    echo "Docker logs:"
    docker-compose logs chromadb 2>/dev/null || echo "No logs available"
fi

echo ""
echo "8️⃣ Final system status..."
echo "------------------------"
echo "Docker containers:"
docker ps
echo ""
echo "Port 8002 status:"
sudo netstat -tlnp | grep :8002 || echo "Port 8002 is free"
