#!/bin/bash

echo "📊 RAG Document Chat - Production Monitoring"
echo "============================================"

API_URL="http://localhost:8003"

# Function to check service health
check_service() {
    local service_name="$1"
    local check_command="$2"
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ $service_name: Healthy"
        return 0
    else
        echo "❌ $service_name: Unhealthy"
        return 1
    fi
}

# Function to get service metrics
get_metrics() {
    echo ""
    echo "📈 System Metrics"
    echo "─────────────────"
    
    # API Server Process
    API_PID=$(pgrep -f "uvicorn.*app_refactored")
    if [ -n "$API_PID" ]; then
        echo "🔧 API Server (PID: $API_PID)"
        ps -p $API_PID -o pid,ppid,pcpu,pmem,etime,cmd --no-headers
        
        # Memory usage
        API_MEM=$(ps -p $API_PID -o pmem --no-headers | tr -d ' ')
        echo "   Memory: ${API_MEM}%"
        
        # CPU usage
        API_CPU=$(ps -p $API_PID -o pcpu --no-headers | tr -d ' ')
        echo "   CPU: ${API_CPU}%"
    else
        echo "❌ API Server: Not running"
    fi
    
    # ChromaDB Container
    echo ""
    echo "🗄️ ChromaDB Container"
    CHROMADB_CONTAINER=$(docker ps -q --filter name=chromadb)
    if [ -n "$CHROMADB_CONTAINER" ]; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" $CHROMADB_CONTAINER
    else
        echo "❌ ChromaDB Container: Not running"
    fi
    
    # Disk usage
    echo ""
    echo "💾 Disk Usage"
    df -h . | tail -1 | awk '{print "   Used: " $3 "/" $2 " (" $5 ")"}'
    
    # Check log file sizes
    echo ""
    echo "📋 Log Files"
    for log_file in api_production.log api_server.log streamlit.log; do
        if [ -f "$log_file" ]; then
            size=$(du -h "$log_file" | cut -f1)
            echo "   $log_file: $size"
        fi
    done
}

# Function to show recent errors
show_recent_errors() {
    echo ""
    echo "🚨 Recent Errors (last 10 lines)"
    echo "─────────────────────────────────"
    
    if [ -f "api_production.log" ]; then
        echo "📄 API Server Errors:"
        grep -i "error\|exception\|failed" api_production.log | tail -5
    fi
    
    # ChromaDB errors
    CHROMADB_CONTAINER=$(docker ps -q --filter name=chromadb)
    if [ -n "$CHROMADB_CONTAINER" ]; then
        echo ""
        echo "📄 ChromaDB Errors:"
        docker logs --tail 5 $CHROMADB_CONTAINER 2>&1 | grep -i "error\|exception\|failed" || echo "   No recent errors"
    fi
}

# Function to test API endpoints
test_endpoints() {
    echo ""
    echo "🔧 API Endpoint Tests"
    echo "────────────────────"
    
    source rag_env/bin/activate
    
    # Test each endpoint
    endpoints=(
        "status:GET:/"
        "documents:GET:/api/documents"
        "collections:GET:/api/collections"
    )
    
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r name method path <<< "$endpoint"
        
        echo -n "   $name: "
        if curl -s -f -X $method "$API_URL$path" > /dev/null; then
            echo "✅ OK"
        else
            echo "❌ FAIL"
        fi
    done
    
    # Test CLI
    echo -n "   CLI Status: "
    if python3 cli.py --api-url $API_URL status > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "❌ FAIL"
    fi
}

# Function to show database stats
show_database_stats() {
    echo ""
    echo "📊 Database Statistics"
    echo "─────────────────────"
    
    source rag_env/bin/activate
    
    # Get collection stats via CLI
    python3 cli.py --api-url $API_URL collections 2>/dev/null | grep -E "(Collections|items|Documents)" || echo "Unable to fetch database stats"
}

# Main monitoring loop
main() {
    while true; do
        clear
        echo "📊 RAG Document Chat - Production Monitoring"
        echo "============================================"
        echo "$(date)"
        echo ""
        
        # Health checks
        echo "🏥 Health Checks"
        echo "───────────────"
        check_service "API Server" "curl -s $API_URL > /dev/null"
        check_service "ChromaDB" "curl -s http://localhost:8002/api/v2/heartbeat > /dev/null"
        check_service "Virtual Environment" "source rag_env/bin/activate && python3 -c 'import fastapi, openai, chromadb'"
        
        # Get metrics
        get_metrics
        
        # Test endpoints
        test_endpoints
        
        # Database stats
        show_database_stats
        
        # Recent errors
        show_recent_errors
        
        echo ""
        echo "────────────────────────────────────────"
        echo "🔄 Refreshing in 30 seconds... (Ctrl+C to exit)"
        echo "📋 Commands: [R]efresh now, [L]ogs, [T]est, [Q]uit"
        
        # Wait for input or timeout
        read -t 30 -n 1 input
        case $input in
            r|R)
                continue
                ;;
            l|L)
                echo ""
                echo "📋 Recent API Logs (last 20 lines):"
                tail -20 api_production.log 2>/dev/null || echo "No logs available"
                read -p "Press Enter to continue..."
                ;;
            t|T)
                echo ""
                echo "🧪 Running quick test..."
                source rag_env/bin/activate
                python3 cli.py --api-url $API_URL status
                read -p "Press Enter to continue..."
                ;;
            q|Q)
                echo ""
                echo "👋 Monitoring stopped"
                exit 0
                ;;
        esac
    done
}

# Check if running in interactive mode
if [ -t 0 ]; then
    main
else
    # Non-interactive mode - just show current status
    echo "🏥 Health Checks"
    check_service "API Server" "curl -s $API_URL > /dev/null"
    check_service "ChromaDB" "curl -s http://localhost:8002/api/v2/heartbeat > /dev/null"
    get_metrics
    test_endpoints
    show_database_stats
fi