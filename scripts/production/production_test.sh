#!/bin/bash

echo "🧪 RAG Document Chat - Production Testing"
echo "========================================="

# Get API URL from config
API_URL=$(python3 -c "from config import config; print(config.api_url)" 2>/dev/null || echo "http://localhost:8003")

# Function to run CLI commands with error handling
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_success="$3"
    
    echo ""
    echo "🔧 TEST: $test_name"
    echo "─────────────────────────────────────────"
    echo "Command: $command"
    echo ""
    
    if source rag_env/bin/activate && eval "$command"; then
        if [ "$expected_success" = "true" ]; then
            echo "✅ PASS: $test_name"
        else
            echo "❌ UNEXPECTED SUCCESS: $test_name"
        fi
    else
        if [ "$expected_success" = "false" ]; then
            echo "✅ PASS: $test_name (expected failure)"
        else
            echo "❌ FAIL: $test_name"
        fi
    fi
    
    echo "═════════════════════════════════════════"
}

# Activate virtual environment
source rag_env/bin/activate

echo "📋 Production Test Suite"
echo "Testing API URL: $API_URL"

# Test 1: System Status
run_test "System Status Check" \
    "python3 cli.py --api-url $API_URL status" \
    "true"

# Test 2: List Documents
run_test "Document Inventory" \
    "python3 cli.py --api-url $API_URL list" \
    "true"

# Test 3: Collections Info
run_test "Collections Information" \
    "python3 cli.py --api-url $API_URL collections" \
    "true"

# Test 4: API Documentation (check if accessible)
run_test "API Documentation Access" \
    "curl -s $API_URL/docs | grep -q 'FastAPI'" \
    "true"

echo ""
echo "📄 Testing with sample document..."

# Create a test document
cat > production_test_doc.txt << 'EOF'
# Production Test Document

This is a comprehensive test document for the RAG Document Chat system in production mode.

## Machine Learning Overview

Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make predictions or decisions.

## Key Concepts

1. **Supervised Learning**: Uses labeled training data to learn patterns
2. **Unsupervised Learning**: Finds hidden patterns in unlabeled data  
3. **Deep Learning**: Uses neural networks with multiple layers
4. **Natural Language Processing**: Enables computers to understand human language

## Applications

Machine learning is used in:
- Image recognition and computer vision
- Natural language translation
- Recommendation systems
- Fraud detection
- Autonomous vehicles
- Medical diagnosis

## Benefits

The main benefits include:
- Automation of complex tasks
- Improved decision making
- Pattern recognition at scale
- Personalized user experiences
- Predictive analytics

This document serves as a test case for document processing, search, and question-answering capabilities.
EOF

# Test 5: Document Upload
run_test "Document Upload" \
    "python3 cli.py --api-url $API_URL process upload production_test_doc.txt" \
    "true"

# Test 6: Generate Summaries
run_test "Generate Summaries" \
    "python3 cli.py --api-url $API_URL process summaries production_test_doc.txt" \
    "true"

# Test 7: Generate Paragraphs
run_test "Generate Paragraphs" \
    "python3 cli.py --api-url $API_URL process paragraphs production_test_doc.txt" \
    "true"

# Wait a moment for processing
echo "⏳ Waiting for document processing to complete..."
sleep 3

# Test 8: Search Functionality
run_test "Basic Search" \
    "python3 cli.py --api-url $API_URL search 'machine learning' --top-k 5" \
    "true"

# Test 9: Search with Save
run_test "Search with Save Results" \
    "python3 cli.py --api-url $API_URL search 'neural networks' --save ml_prod_search.json --top-k 3" \
    "true"

# Test 10: Document-Specific Search
run_test "Document-Specific Search" \
    "python3 cli.py --api-url $API_URL search 'deep learning' --documents production_test_doc.txt" \
    "true"

# Test 11: Collection-Specific Search
run_test "Collection-Specific Search" \
    "python3 cli.py --api-url $API_URL search 'artificial intelligence' --collections documents" \
    "true"

# Test 12: Ask Question
run_test "Basic Question" \
    "python3 cli.py --api-url $API_URL ask 'What is machine learning?'" \
    "true"

# Test 13: Ask with Search Results
if [ -f "ml_prod_search.json" ]; then
    run_test "Ask with Cached Search" \
        "python3 cli.py --api-url $API_URL ask 'Explain neural networks' --from-search ml_prod_search.json" \
        "true"
fi

# Test 14: Ask Document-Specific Question
run_test "Document-Specific Question" \
    "python3 cli.py --api-url $API_URL ask 'What are the benefits mentioned in this document?' --documents production_test_doc.txt" \
    "true"

# Test 15: Load Testing (multiple rapid requests)
echo ""
echo "🚀 Load Testing (10 rapid requests)..."
for i in {1..10}; do
    echo -n "$i "
    python3 cli.py --api-url $API_URL search "test query $i" --top-k 2 > /dev/null 2>&1 &
done
wait
echo ""
echo "✅ Load test completed"

# Test 16: Error Handling
run_test "Error Handling - Invalid File" \
    "python3 cli.py --api-url $API_URL process upload nonexistent_file.txt" \
    "false"

run_test "Error Handling - Invalid Document" \
    "python3 cli.py --api-url $API_URL process summaries nonexistent_document.txt" \
    "false"

# Performance Tests
echo ""
echo "⚡ Performance Tests"
echo "─────────────────────"

# Large search test
echo "Testing search performance..."
start_time=$(date +%s%N)
python3 cli.py --api-url $API_URL search "comprehensive test document machine learning" --top-k 20 > /dev/null 2>&1
end_time=$(date +%s%N)
search_duration=$(( (end_time - start_time) / 1000000 ))
echo "✅ Large search completed in ${search_duration}ms"

# Complex question test
echo "Testing complex question performance..."
start_time=$(date +%s%N)
python3 cli.py --api-url $API_URL ask "Compare supervised and unsupervised learning approaches, explaining their key differences and use cases" > /dev/null 2>&1
end_time=$(date +%s%N)
ask_duration=$(( (end_time - start_time) / 1000000 ))
echo "✅ Complex question completed in ${ask_duration}ms"

# Final system check
echo ""
echo "📊 Final System Status"
echo "─────────────────────"
python3 cli.py --api-url $API_URL list
python3 cli.py --api-url $API_URL collections

echo ""
echo "🎉 Production Testing Complete!"
echo ""
echo "📈 Performance Summary:"
echo "   Search Time: ${search_duration}ms"
echo "   Question Time: ${ask_duration}ms"
echo ""
echo "🧹 Cleanup:"
echo "   Test document: production_test_doc.txt"
echo "   Search results: ml_prod_search.json"
echo ""
echo "💡 Tips for production use:"
echo "   1. Monitor API logs: tail -f api_production.log"
echo "   2. Use --save for expensive searches to reuse results"
echo "   3. Filter by documents/collections for better performance"
echo "   4. Use document-specific questions for more accurate answers"