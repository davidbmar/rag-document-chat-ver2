#!/usr/bin/env python3
"""
Working CLI Interface - Direct RAG System Access
Usage: python3 working_cli.py search "query"
       python3 working_cli.py ask "question"
"""

import sys
import asyncio
sys.path.append('.')

from src.search.rag_system import RAGSystem

async def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 working_cli.py search 'your search query'")
        print("  python3 working_cli.py ask 'your question'")
        sys.exit(1)
    
    command = sys.argv[1]
    query = sys.argv[2]
    
    rag = RAGSystem()
    
    if command == "search":
        print(f"🔍 Searching for: '{query}'")
        print("─" * 50)
        
        try:
            response = rag.search_and_answer(query, top_k=5)
            
            print(f"📊 Search Results:")
            print(f"   Query: {query}")
            print(f"   Found relevant information")
            
            if hasattr(response, 'sources') and response.sources:
                print(f"   Sources: {len(response.sources)} document chunks")
            
            print(f"\n📝 Content Preview:")
            preview = response.answer[:300].replace('\n', ' ')
            print(f"   {preview}...")
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    elif command == "ask":
        print(f"❓ Question: '{query}'")
        print("─" * 50)
        
        try:
            response = rag.search_and_answer(query, top_k=5)
            
            print(f"💬 Answer:")
            print(f"{response.answer}")
            
            if hasattr(response, 'sources') and response.sources:
                print(f"\n📚 Sources: {len(response.sources)} document sections")
            
        except Exception as e:
            print(f"❌ Q&A failed: {e}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'search' or 'ask'")

if __name__ == "__main__":
    asyncio.run(main())