#!/bin/bash

echo "🚀 RAG Document Chat - Chained Search-Ask Workflow Demo"
echo "======================================================="

# Check if API server is running
echo "🔍 Checking API server status..."
python3 cli.py status || {
    echo "❌ API server not running. Please start it first:"
    echo "   python3 app_refactored.py"
    exit 1
}

echo ""
echo "📚 Current documents in system:"
python3 cli.py list

echo ""
echo "🔍 Step 1: Search for content about 'machine learning'"
echo "─────────────────────────────────────────────────────"
python3 cli.py search "machine learning" --top-k 5 --save ml_search.json --verbose

echo ""
echo "💬 Step 2: Ask a question using the search results"
echo "─────────────────────────────────────────────────────"
python3 cli.py ask "What are the main benefits of machine learning?" --from-search ml_search.json

echo ""
echo "🎯 Step 3: Search for specific documents and ask targeted questions"
echo "──────────────────────────────────────────────────────────────────"
python3 cli.py search "neural networks" --documents "ai_textbook.pdf" --save neural_search.json
python3 cli.py ask "How do neural networks learn?" --from-search neural_search.json

echo ""
echo "🤖 Step 4: Interactive chat mode (use /quit to exit)"
echo "──────────────────────────────────────────────────────"
echo "Commands available in interactive mode:"
echo "  /search <query>     - Search and save results"
echo "  /load <file>        - Load search results from file"
echo "  /quit               - Exit interactive mode"
echo ""
python3 cli.py ask "dummy" --interactive

echo ""
echo "✅ Demo completed!"