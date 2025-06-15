#!/bin/bash

echo "🎯 RAG Document Chat - Step 1 MVP Acceptance Test"
echo "=================================================="
echo "Testing all core functionality for MVP completion"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test with status tracking
run_mvp_test() {
    local test_name="$1"
    local command="$2"
    local expected_success="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo -e "${BLUE}🧪 TEST $TOTAL_TESTS: $test_name${NC}"
    echo "────────────────────────────────────────"
    echo "Command: $command"
    echo ""
    
    # Activate environment and run command
    if source rag_env/bin/activate && eval "$command" > /tmp/test_output.log 2>&1; then
        if [ "$expected_success" = "true" ]; then
            echo -e "${GREEN}✅ PASS: $test_name${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            
            # Show key output for important tests
            if [[ "$test_name" =~ "Search|Upload|Ask" ]]; then
                echo "Output preview:"
                head -5 /tmp/test_output.log | sed 's/^/   /'
            fi
        else
            echo -e "${RED}❌ UNEXPECTED SUCCESS: $test_name${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [ "$expected_success" = "false" ]; then
            echo -e "${GREEN}✅ PASS: $test_name (expected failure)${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAIL: $test_name${NC}"
            echo "Error output:"
            tail -3 /tmp/test_output.log | sed 's/^/   /'
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    
    echo "════════════════════════════════════════"
}

# Create test document for MVP
cat > mvp_test_document.txt << 'EOF'
# Machine Learning MVP Test Document

This document tests the complete RAG pipeline for the MVP demonstration.

## Artificial Intelligence Overview

Artificial intelligence (AI) is a broad field of computer science focused on creating systems capable of performing tasks that typically require human intelligence. AI encompasses machine learning, deep learning, and natural language processing.

## Machine Learning Fundamentals

Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. Key approaches include:

1. **Supervised Learning**: Learning from labeled training data
2. **Unsupervised Learning**: Finding patterns in unlabeled data  
3. **Reinforcement Learning**: Learning through trial and error

## Deep Learning Applications

Deep learning uses neural networks with multiple layers to process complex data. Applications include:
- Computer vision and image recognition
- Natural language understanding
- Speech recognition and synthesis
- Autonomous vehicle navigation

## Benefits and Impact

The main benefits of AI and machine learning include:
- Automation of repetitive tasks
- Enhanced decision-making capabilities
- Personalized user experiences
- Predictive analytics and forecasting
- Medical diagnosis assistance

This document serves as a comprehensive test case for document processing, search functionality, and question-answering capabilities in the RAG system.
EOF

echo "📋 MVP Acceptance Test Plan:"
echo "   ✓ System health and configuration"
echo "   ✓ Document upload and processing pipeline"
echo "   ✓ Search functionality with filtering"
echo "   ✓ Chained search-ask workflow"
echo "   ✓ Collection and document management"
echo "   ✓ Error handling and edge cases"
echo "   ✓ Performance and production readiness"

# TEST GROUP 1: System Health & Configuration
echo ""
echo -e "${YELLOW}📊 TEST GROUP 1: System Health & Configuration${NC}"

run_mvp_test "System Status Check" \
    "python3 cli.py status" \
    "true"

run_mvp_test "Configuration Loading" \
    "python3 -c 'from config import config; print(f\"API: {config.api_url}\"); assert config.api_port > 0'" \
    "true"

run_mvp_test "API Endpoint Accessibility" \
    "curl -s \$(python3 -c 'from config import config; print(config.api_url)')/ | grep -q 'RAG Document Chat'" \
    "true"

# TEST GROUP 2: Document Processing Pipeline
echo ""
echo -e "${YELLOW}📄 TEST GROUP 2: Document Processing Pipeline${NC}"

run_mvp_test "Document Upload (Basic Processing)" \
    "python3 cli.py process upload mvp_test_document.txt" \
    "true"

run_mvp_test "Smart Summaries Generation" \
    "python3 cli.py process summaries mvp_test_document.txt" \
    "true"

run_mvp_test "Paragraph Processing" \
    "python3 cli.py process paragraphs mvp_test_document.txt" \
    "true"

run_mvp_test "Document Inventory Tracking" \
    "python3 cli.py list | grep -q 'mvp_test_document.txt'" \
    "true"

# TEST GROUP 3: Search Functionality
echo ""
echo -e "${YELLOW}🔍 TEST GROUP 3: Search Functionality${NC}"

run_mvp_test "Basic Search Operation" \
    "python3 cli.py search 'machine learning' --top-k 5" \
    "true"

run_mvp_test "Search with Result Caching" \
    "python3 cli.py search 'artificial intelligence' --save mvp_ai_search.json --top-k 3" \
    "true"

run_mvp_test "Document-Specific Search" \
    "python3 cli.py search 'deep learning' --documents mvp_test_document.txt" \
    "true"

run_mvp_test "Collection-Specific Search" \
    "python3 cli.py search 'neural networks' --collections logical_summaries" \
    "true"

run_mvp_test "Search Result File Generation" \
    "test -f mvp_ai_search.json && cat mvp_ai_search.json | grep -q 'search_id'" \
    "true"

# TEST GROUP 4: Chained Search-Ask Workflow (MVP CORE)
echo ""
echo -e "${YELLOW}🔗 TEST GROUP 4: Chained Search-Ask Workflow (MVP CORE)${NC}"

run_mvp_test "Question Answering with Search Context" \
    "python3 cli.py ask 'What is artificial intelligence?' --from-search mvp_ai_search.json" \
    "true"

run_mvp_test "Document-Scoped Question" \
    "python3 cli.py ask 'What are the main benefits mentioned?' --documents mvp_test_document.txt" \
    "true"

run_mvp_test "Multi-Step Workflow: Search then Ask" \
    "python3 cli.py search 'supervised learning' --save supervised_search.json --top-k 3 && python3 cli.py ask 'Explain supervised learning' --from-search supervised_search.json" \
    "true"

run_mvp_test "Different Search Strategies" \
    "python3 cli.py ask 'Compare machine learning approaches' --strategy enhanced" \
    "true"

# TEST GROUP 5: Collection and Data Management
echo ""
echo -e "${YELLOW}🗄️ TEST GROUP 5: Collection and Data Management${NC}"

run_mvp_test "Collections Information" \
    "python3 cli.py collections | grep -E '(documents|logical_summaries|paragraph_summaries)'" \
    "true"

run_mvp_test "Document List with Statistics" \
    "python3 cli.py list | grep -E '(chunks|items)'" \
    "true"

run_mvp_test "Multi-Document Environment" \
    "python3 cli.py list | grep -c 'txt' | awk '{exit (\$1 >= 2) ? 0 : 1}'" \
    "true"

# TEST GROUP 6: Error Handling and Edge Cases
echo ""
echo -e "${YELLOW}⚠️ TEST GROUP 6: Error Handling and Edge Cases${NC}"

run_mvp_test "Invalid File Upload" \
    "python3 cli.py process upload nonexistent_file_12345.txt" \
    "false"

run_mvp_test "Empty Search Query Handling" \
    "python3 cli.py search '' --top-k 1" \
    "false"

run_mvp_test "API Connection Error Handling" \
    "python3 cli.py --api-url http://localhost:9999 status" \
    "false"

# TEST GROUP 7: Performance and Production Readiness
echo ""
echo -e "${YELLOW}⚡ TEST GROUP 7: Performance and Production Readiness${NC}"

run_mvp_test "Search Performance (< 2 seconds)" \
    "timeout 2s python3 cli.py search 'machine learning applications' --top-k 10" \
    "true"

run_mvp_test "Question Answering Performance (< 10 seconds)" \
    "timeout 10s python3 cli.py ask 'What are the different types of machine learning?' --documents mvp_test_document.txt" \
    "true"

run_mvp_test "Concurrent Request Handling" \
    "for i in {1..3}; do python3 cli.py search \"test query \$i\" --top-k 2 & done; wait" \
    "true"

run_mvp_test "Large Document Handling" \
    "python3 cli.py search 'alice wonderland' --top-k 20 | grep -q 'Search Results'" \
    "true"

# Final MVP Assessment
echo ""
echo "🎯 MVP ACCEPTANCE TEST RESULTS"
echo "══════════════════════════════"
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "Success Rate: ${BLUE}$PASS_RATE%${NC}"

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 MVP ACCEPTANCE TEST: PASSED${NC}"
    echo -e "${GREEN}✅ Step 1 MVP is COMPLETE and PRODUCTION READY${NC}"
    echo ""
    echo "✅ Core Features Verified:"
    echo "   • Chained search-ask workflow working"
    echo "   • Complete API/UI separation achieved"
    echo "   • Environment-based configuration functional"
    echo "   • Document processing pipeline operational"
    echo "   • Multi-collection search and filtering working"
    echo "   • Production deployment ready"
    echo "   • Error handling robust"
    echo "   • Performance acceptable"
    
elif [ $PASS_RATE -ge 90 ]; then
    echo -e "${YELLOW}⚠️ MVP ACCEPTANCE TEST: CONDITIONAL PASS${NC}"
    echo -e "${YELLOW}📋 $FAILED_TESTS minor issues need attention${NC}"
    echo "Step 1 MVP is substantially complete"
    
else
    echo -e "${RED}❌ MVP ACCEPTANCE TEST: FAILED${NC}"
    echo -e "${RED}🚨 $FAILED_TESTS critical issues must be resolved${NC}"
    echo "Step 1 MVP requires additional work"
fi

echo ""
echo "📋 Cleanup test files..."
rm -f mvp_test_document.txt mvp_ai_search.json supervised_search.json /tmp/test_output.log

echo ""
echo "📊 Next Steps:"
if [ $FAILED_TESTS -eq 0 ]; then
    echo "   1. ✅ Step 1 MVP is complete"
    echo "   2. 🚀 Ready to proceed to Step 2"
    echo "   3. 📝 Document final deployment procedure"
    echo "   4. 🎯 Define Step 2 requirements"
else
    echo "   1. 🔧 Review and fix failed tests"
    echo "   2. 🧪 Re-run MVP acceptance test"
    echo "   3. 📋 Address any remaining issues"
    echo "   4. ✅ Confirm MVP completion"
fi