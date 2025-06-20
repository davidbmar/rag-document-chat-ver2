#!/usr/bin/env python3
"""
Command Line Interface for RAG Document Chat System
"""

import os
import sys
import json
import argparse
import requests
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import config to get default API URL
try:
    from src.core.config import config
    DEFAULT_API_URL = config.api_url
except ImportError:
    # Fallback if config import fails
    DEFAULT_API_URL = "http://localhost:8003"


class RAGClient:
    """CLI client for RAG Document Chat API"""
    
    def __init__(self, api_url: str = DEFAULT_API_URL):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make HTTP request to API"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Status: {e.response.status_code}")
            sys.exit(1)
    
    def search(self, query: str, top_k: int = 10, collections: Optional[List[str]] = None,
               documents: Optional[List[str]] = None, exclude_documents: Optional[List[str]] = None,
               threshold: Optional[float] = None, save_results: Optional[str] = None) -> Dict[Any, Any]:
        """Search documents with filtering"""
        print(f"🔍 Searching for: '{query}'")
        
        payload = {
            "query": query,
            "top_k": top_k,
            "return_chunks": True
        }
        
        if collections:
            payload["collections"] = collections
        if documents:
            payload["documents"] = documents
        if exclude_documents:
            payload["exclude_documents"] = exclude_documents
        if threshold:
            payload["threshold"] = threshold
        
        result = self._make_request("POST", "/api/search", json=payload)
        
        # Save results if requested
        if save_results:
            with open(save_results, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Search results saved to: {save_results}")
        
        return result
    
    def ask(self, question: str, top_k: int = 8, documents: Optional[List[str]] = None,
            exclude_documents: Optional[List[str]] = None, chunk_ids: Optional[List[str]] = None,
            search_id: Optional[str] = None, conversation_history: str = "",
            search_strategy: str = "enhanced", from_search_file: Optional[str] = None) -> Dict[Any, Any]:
        """Ask questions with context filtering"""
        print(f"💬 Question: '{question}'")
        
        payload = {
            "question": question,
            "top_k": top_k,
            "conversation_history": conversation_history,
            "search_strategy": search_strategy
        }
        
        # Handle search result reuse
        if from_search_file:
            try:
                with open(from_search_file, 'r') as f:
                    search_data = json.load(f)
                payload["search_id"] = search_data.get("search_id")
                print(f"📋 Using search results from: {from_search_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load search file {from_search_file}: {e}")
        elif search_id:
            payload["search_id"] = search_id
        elif documents:
            payload["documents"] = documents
        elif exclude_documents:
            payload["exclude_documents"] = exclude_documents
        elif chunk_ids:
            payload["chunk_ids"] = chunk_ids
        
        result = self._make_request("POST", "/api/ask", json=payload)
        return result
    
    def upload(self, file_path: str) -> Dict[Any, Any]:
        """Upload and process a document"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ Error: File not found: {file_path}")
            sys.exit(1)
        
        if not file_path.suffix.lower() in ['.pdf', '.txt']:
            print(f"❌ Error: Unsupported file type. Only PDF and TXT files are supported.")
            sys.exit(1)
        
        print(f"📄 Uploading: {file_path.name}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            result = self._make_request("POST", "/api/process/upload", files=files)
        
        return result
    
    def process_summaries(self, filename: str) -> Dict[Any, Any]:
        """Generate smart summaries for a document"""
        print(f"🧠 Processing summaries for: {filename}")
        result = self._make_request("POST", f"/api/process/{filename}/summaries")
        return result
    
    def process_paragraphs(self, filename: str) -> Dict[Any, Any]:
        """Generate paragraph summaries for a document"""
        print(f"📝 Processing paragraphs for: {filename}")
        result = self._make_request("POST", f"/api/process/{filename}/paragraphs")
        return result
    
    def list_documents(self) -> Dict[Any, Any]:
        """List all processed documents"""
        print("📚 Listing documents...")
        result = self._make_request("GET", "/api/documents")
        return result
    
    def clear_documents(self) -> Dict[Any, Any]:
        """Clear all documents"""
        print("🧹 Clearing all documents...")
        result = self._make_request("DELETE", "/api/documents")
        return result
    
    def get_collections(self) -> Dict[Any, Any]:
        """Get collections information"""
        print("🗄️ Getting collections info...")
        result = self._make_request("GET", "/api/collections")
        return result
    
    def get_status(self) -> Dict[Any, Any]:
        """Get system status"""
        result = self._make_request("GET", "/status")
        return result


def format_search_results(results: Dict[Any, Any], verbose: bool = False):
    """Format and display search results"""
    print(f"\n🔍 Search Results ({results['total_results']} found in {results['processing_time']:.2f}s)")
    print(f"   Search ID: {results['search_id']}")
    print(f"   Collections: {', '.join(results['collections_searched'])}")
    print(f"   Documents: {', '.join(results['unique_documents'])}")
    
    if results['results']:
        print("\n📄 Top Results:")
        for i, result in enumerate(results['results'][:10], 1):
            score_bar = "█" * int(result['score'] * 10)
            print(f"   {i:2d}. [{score_bar:<10}] {result['score']:.3f} - {result['document']}")
            print(f"       Collection: {result['collection']} | Chunk: {result['chunk_id']}")
            
            if verbose:
                content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                print(f"       Content: {content}")
            print()
    else:
        print("   No results found.")


def format_ask_response(response: Dict[Any, Any]):
    """Format and display ask response"""
    print(f"\n💬 Answer (generated in {response['processing_time']:.2f}s):")
    print("─" * 60)
    print(response['answer'])
    print("─" * 60)
    
    if response['sources']:
        print(f"\n📚 Sources ({len(response['sources'])}):")
        for source in response['sources']:
            print(f"   • {source}")


def format_document_list(doc_list: Dict[Any, Any]):
    """Format and display document list"""
    print(f"\n📚 Document Inventory ({doc_list['total_items']} total items)")
    
    if doc_list['documents']:
        print("\n📄 Documents:")
        for filename, data in doc_list['documents'].items():
            print(f"   • {filename} ({data['total_chunks']} chunks)")
            for collection, count in data['collections'].items():
                print(f"     └─ {collection}: {count} items")
    else:
        print("   No documents found.")
    
    if doc_list['collections']:
        print(f"\n🗄️ Collections ({len(doc_list['collections'])}):")
        for collection in doc_list['collections']:
            print(f"   • {collection['name']}: {collection['count']} items")


def interactive_chat(client: RAGClient, search_file: Optional[str] = None):
    """Interactive chat mode"""
    print("🤖 Interactive Chat Mode")
    print("Commands: /search <query>, /load <file>, /quit")
    print("─" * 50)
    
    conversation_history = ""
    current_search_file = search_file
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['/quit', '/exit', '/q']:
                print("👋 Goodbye!")
                break
            
            if user_input.startswith('/search '):
                query = user_input[8:].strip()
                if query:
                    results = client.search(query, save_results="last_search.json")
                    format_search_results(results)
                    current_search_file = "last_search.json"
                    print(f"\n💡 Use these results with: rag ask '<question>' --from-search last_search.json")
                continue
            
            if user_input.startswith('/load '):
                file_path = user_input[6:].strip()
                if os.path.exists(file_path):
                    current_search_file = file_path
                    print(f"📋 Loaded search results from: {file_path}")
                else:
                    print(f"❌ File not found: {file_path}")
                continue
            
            # Regular question
            response = client.ask(
                user_input,
                conversation_history=conversation_history,
                from_search_file=current_search_file
            )
            
            print(f"\n🤖 Assistant: {response['answer']}")
            
            if response['sources']:
                print(f"\n📚 Sources: {', '.join(response['sources'])}")
            
            # Update conversation history
            conversation_history += f"\nUser: {user_input}\nAssistant: {response['answer']}"
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="RAG Document Chat CLI")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    search_parser.add_argument("--collections", nargs="+", help="Collections to search")
    search_parser.add_argument("--documents", nargs="+", help="Specific documents to search")
    search_parser.add_argument("--exclude", nargs="+", help="Documents to exclude")
    search_parser.add_argument("--threshold", type=float, help="Minimum similarity score")
    search_parser.add_argument("--save", help="Save results to file")
    search_parser.add_argument("--verbose", "-v", action="store_true", help="Show content preview")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask questions")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument("--top-k", type=int, default=8, help="Number of chunks to use")
    ask_parser.add_argument("--documents", nargs="+", help="Specific documents")
    ask_parser.add_argument("--exclude", nargs="+", help="Documents to exclude")
    ask_parser.add_argument("--chunks", nargs="+", help="Specific chunk IDs")
    ask_parser.add_argument("--search-id", help="Use cached search results")
    ask_parser.add_argument("--from-search", help="Load search results from file")
    ask_parser.add_argument("--strategy", choices=["basic", "enhanced", "paragraph"], 
                           default="enhanced", help="Search strategy")
    ask_parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
    
    # Process commands
    process_parser = subparsers.add_parser("process", help="Process documents")
    process_subparsers = process_parser.add_subparsers(dest="process_command")
    
    upload_parser = process_subparsers.add_parser("upload", help="Upload document")
    upload_parser.add_argument("file", help="File to upload")
    
    summaries_parser = process_subparsers.add_parser("summaries", help="Generate summaries")
    summaries_parser.add_argument("filename", help="Document filename")
    
    paragraphs_parser = process_subparsers.add_parser("paragraphs", help="Generate paragraph summaries")
    paragraphs_parser.add_argument("filename", help="Document filename")
    
    # List command
    subparsers.add_parser("list", help="List documents")
    
    # Clear command
    subparsers.add_parser("clear", help="Clear all documents")
    
    # Collections command
    subparsers.add_parser("collections", help="Show collections info")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    client = RAGClient(args.api_url)
    
    try:
        if args.command == "search":
            results = client.search(
                args.query,
                top_k=args.top_k,
                collections=args.collections,
                documents=args.documents,
                exclude_documents=args.exclude,
                threshold=args.threshold,
                save_results=args.save
            )
            format_search_results(results, verbose=args.verbose)
            
        elif args.command == "ask":
            if args.interactive:
                interactive_chat(client, args.from_search)
            else:
                response = client.ask(
                    args.question,
                    top_k=args.top_k,
                    documents=args.documents,
                    exclude_documents=args.exclude,
                    chunk_ids=args.chunks,
                    search_id=args.search_id,
                    search_strategy=args.strategy,
                    from_search_file=args.from_search
                )
                format_ask_response(response)
                
        elif args.command == "process":
            if args.process_command == "upload":
                result = client.upload(args.file)
                print(f"✅ {result['message']}")
                print(f"   Chunks created: {result['chunks_created']}")
                print(f"   Processing time: {result['processing_time']:.2f}s")
                
            elif args.process_command == "summaries":
                result = client.process_summaries(args.filename)
                print(f"✅ {result['message']}")
                print(f"   Summaries created: {result['chunks_created']}")
                print(f"   Processing time: {result['processing_time']:.2f}s")
                
            elif args.process_command == "paragraphs":
                result = client.process_paragraphs(args.filename)
                print(f"✅ {result['message']}")
                print(f"   Paragraphs processed: {result['chunks_created']}")
                print(f"   Processing time: {result['processing_time']:.2f}s")
                
        elif args.command == "list":
            doc_list = client.list_documents()
            format_document_list(doc_list)
            
        elif args.command == "clear":
            result = client.clear_documents()
            print(f"✅ {result['message']}")
            for collection in result['cleared_collections']:
                print(f"   • {collection['name']}: {collection['items_deleted']} items deleted")
                
        elif args.command == "collections":
            result = client.get_collections()
            print(f"\n🗄️ Collections ({result['total_collections']} total)")
            for collection in result['collections']:
                if 'error' in collection:
                    print(f"   ❌ {collection['name']}: {collection['error']}")
                else:
                    print(f"   • {collection['name']}: {collection['item_count']} items")
                    if collection['unique_documents']:
                        print(f"     Documents: {', '.join(collection['unique_documents'])}")
                        
        elif args.command == "status":
            status = client.get_status()
            print("🔧 System Status:")
            for service, state in status.items():
                if state == "connected":
                    print(f"   ✅ {service.title()}: Connected")
                elif state == "error":
                    print(f"   ❌ {service.title()}: Error")
                else:
                    print(f"   ⚠️ {service.title()}: {state}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()