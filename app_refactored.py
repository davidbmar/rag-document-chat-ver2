#!/usr/bin/env python3
"""
RAG Document Chat System
A complete retrieval augmented generation system for document Q&A
"""

import asyncio
import sys
import logging
from typing import Dict

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

from src.core.config import config
from src.core.models import ChatRequest, ChatResponse, DocumentResponse, SearchRequest, SearchResponse, AskRequest, ProcessRequest
from src.search.rag_system import RAGSystem
from src.core.utils import print_usage, setup_logging

logger = setup_logging()

# Initialize RAG system
rag_system = RAGSystem()

# FastAPI Application
app = FastAPI(
    title="RAG Document Chat API",
    description="Retrieval Augmented Generation system for document Q&A",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RAG Document Chat API is running!",
        "status": rag_system.get_system_status()
    }

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Process document
        result = await rag_system.process_document(content, file.filename)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Ask questions about uploaded documents"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = rag_system.search_and_answer(request.query, request.top_k)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get system status"""
    return rag_system.get_system_status()


# Enhanced API Endpoints for Chained Search-Ask Workflow

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents with filtering and result persistence"""
    try:
        logger.info(f"🔍 API Search request: {request.query}")
        result = rag_system.search_engine.search_documents(request)
        return result
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask", response_model=ChatResponse)
async def ask_question(request: AskRequest):
    """Ask questions with context filtering and search result reuse"""
    try:
        logger.info(f"💬 API Ask request: {request.question}")
        result = rag_system.search_engine.ask_with_context(request)
        return result
    except Exception as e:
        logger.error(f"Ask API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/upload", response_model=DocumentResponse)
async def process_upload(file: UploadFile = File(...)):
    """Upload and process document with basic chunking"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        result = await rag_system.process_document(content, file.filename)
        return result
    except Exception as e:
        logger.error(f"Process upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/{filename}/summaries", response_model=DocumentResponse)
async def process_summaries(filename: str):
    """Generate smart summaries for a processed document"""
    try:
        logger.info(f"🧠 Processing summaries for: {filename}")
        result = await rag_system.process_document_hierarchically(filename)
        return DocumentResponse(
            status=result.status,
            message=result.message,
            chunks_created=result.summaries_created,
            processing_time=result.total_processing_time
        )
    except Exception as e:
        logger.error(f"Process summaries error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/{filename}/paragraphs", response_model=DocumentResponse)
async def process_paragraphs(filename: str):
    """Generate paragraph summaries for a processed document"""
    try:
        logger.info(f"📝 Processing paragraphs for: {filename}")
        result = await rag_system.process_document_paragraphs(filename)
        return DocumentResponse(
            status=result.status,
            message=result.message,
            chunks_created=result.paragraphs_processed,
            processing_time=result.total_processing_time
        )
    except Exception as e:
        logger.error(f"Process paragraphs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents():
    """List all processed documents"""
    try:
        # Get document inventory from ChromaDB
        status_data = {
            'documents': {},
            'total_items': 0,
            'collections': []
        }
        
        # Check all collections
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                items = collection.get()
                
                count = len(items.get('ids', []))
                status_data['total_items'] += count
                status_data['collections'].append({
                    'name': collection_name,
                    'count': count
                })
                
                # Track documents
                if 'metadatas' in items and items['metadatas']:
                    for metadata in items['metadatas']:
                        if isinstance(metadata, dict) and 'filename' in metadata:
                            filename = metadata['filename']
                            if filename not in status_data['documents']:
                                status_data['documents'][filename] = {
                                    'collections': {},
                                    'total_chunks': 0
                                }
                            
                            if collection_name not in status_data['documents'][filename]['collections']:
                                status_data['documents'][filename]['collections'][collection_name] = 0
                            
                            status_data['documents'][filename]['collections'][collection_name] += 1
                            status_data['documents'][filename]['total_chunks'] += 1
                            
            except Exception as e:
                logger.warning(f"Error accessing collection {collection_name}: {e}")
        
        return status_data
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents")
async def clear_all_documents():
    """Clear all documents and reset system"""
    try:
        logger.info("🧹 API Clear all documents request")
        
        # Get all collections
        collections = rag_system.clients.chromadb.client.list_collections()
        cleared_collections = []
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                
                # Get all items to count them
                items = collection.get()
                item_count = len(items.get('ids', []))
                
                if item_count > 0:
                    # Clear the collection
                    collection.delete(ids=items['ids'])
                    cleared_collections.append({
                        'name': collection_name,
                        'items_deleted': item_count
                    })
                    
            except Exception as e:
                logger.warning(f"Error clearing collection {collection_name}: {e}")
        
        return {
            'status': 'success',
            'message': f'Cleared {len(cleared_collections)} collections',
            'cleared_collections': cleared_collections
        }
        
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections")
async def get_collections_info():
    """Get detailed information about all ChromaDB collections"""
    try:
        collections_info = []
        
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                items = collection.get()
                
                # Extract unique filenames
                filenames = set()
                if 'metadatas' in items and items['metadatas']:
                    for metadata in items['metadatas']:
                        if isinstance(metadata, dict) and 'filename' in metadata:
                            filenames.add(metadata['filename'])
                
                collections_info.append({
                    'name': collection_name,
                    'item_count': len(items.get('ids', [])),
                    'unique_documents': list(filenames),
                    'sample_ids': items.get('ids', [])[:3]
                })
                
            except Exception as e:
                collections_info.append({
                    'name': collection_name,
                    'error': str(e)
                })
        
        return {
            'collections': collections_info,
            'total_collections': len(collections_info)
        }
        
    except Exception as e:
        logger.error(f"Collections info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Streamlit Interface
def create_streamlit_app():
    """Create Streamlit web interface"""
    
    if not STREAMLIT_AVAILABLE:
        print("Streamlit is not installed. Please install it with: pip install streamlit")
        return
    
    st.set_page_config(
        page_title="RAG Document Chat",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 RAG Document Chat System")
    st.markdown("Upload documents and chat with them using AI!")

    # File upload section
    st.header("📁 Document Processing")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'txt'],
        help="Upload PDF or TXT files to add to your knowledge base"
    )
    
    if uploaded_file is not None:
        # Step 1: Basic Processing
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Basic Chunks", use_container_width=True, help="Process into logical chunks"):
                with st.spinner("Creating logical chunks..."):
                    try:
                        result = asyncio.run(rag_system.process_document(
                            uploaded_file.read(), uploaded_file.name
                        ))
                        
                        if result.status == "success":
                            st.success(f"✅ {result.message}")
                            st.info(f"⏱️ Processed in {result.processing_time:.2f}s")
                            
                            # Store filename for step 2
                            st.session_state['last_processed_file'] = uploaded_file.name
                        else:
                            st.error(f"❌ {result.message}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Step 2: Enhanced Processing (only available after step 1)
        with col2:
            if 'last_processed_file' in st.session_state and st.session_state['last_processed_file'] == uploaded_file.name:
                if st.button("🧠 Smart Summaries", use_container_width=True, help="Add 10:1 compressed summaries"):
                    with st.spinner("Creating smart summaries (10:1 compression)..."):
                        try:
                            result = asyncio.run(
                                rag_system.process_document_hierarchically(
                                    uploaded_file.name
                                )
                            )
                            
                            if result.status == "success":
                                st.success(f"✅ {result.message}")
                                
                                # Show compression stats
                                stats = result.compression_stats
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.metric(
                                        "Logical Groups", 
                                        result.logical_groups_created
                                    )
                                
                                with col_b:
                                    st.metric(
                                        "Compression Ratio", 
                                        f"{stats.get('overall_compression_ratio', 0):.1f}:1"
                                    )
                                
                                with col_c:
                                    st.metric(
                                        "Processing Time", 
                                        f"{result.total_processing_time:.1f}s"
                                    )
                                
                                # Show word reduction
                                input_words = stats.get('total_input_words', 0)
                                output_words = stats.get('total_output_words', 0)
                                
                                st.info(f"📊 Compressed {input_words:,} words → {output_words:,} words")
                                
                            else:
                                st.error(f"❌ {result.message}")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            else:
                st.button("🧠 Smart Summaries", use_container_width=True, disabled=True, help="Process basic chunks first")
        
        # Add processing status
        st.divider()
        st.subheader("📊 Processing Status")
        
        # Check what collections exist
        try:
            basic_count = len(rag_system.clients.chromadb.get_or_create_collection("documents").get()['ids'])
            
            summary_count = 0
            try:
                summary_collection = rag_system.clients.chromadb.get_or_create_collection("logical_summaries")
                summary_count = len(summary_collection.get()['ids'])
            except:
                summary_count = 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Basic Chunks", basic_count)
            with col2:
                st.metric("Smart Summaries", summary_count)
                
        except Exception as e:
            st.warning("Could not retrieve processing stats")

    
    # Main chat interface
    st.header("💬 Chat with Your Documents")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources for assistant messages
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Sources", expanded=False):
                    for source in message["sources"]:
                        st.text(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    try:
                        summary_collection = rag_system.clients.chromadb.get_or_create_collection("logical_summaries")
                        has_summaries = len(summary_collection.get()['ids']) > 0
                    except:
                        has_summaries = False
                    
                    if has_summaries:
                        response = rag_system.search_enhanced(prompt, top_k=8, use_summaries=True)
                        st.caption("🧠 Using smart summaries + detailed chunks")
                    else:
                        response = rag_system.search_and_answer(prompt, top_k=8)
                        st.caption("📄 Using basic chunks only")
                    
                    # Display answer
                    st.markdown(response.answer)
                    
                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "sources": response.sources
                    })
                    
                    # Show sources
                    if response.sources:
                        with st.expander("📚 Sources", expanded=False):
                            for source in response.sources:
                                if source.startswith("Summary:"):
                                    st.markdown(f"🧠 {source}")
                                else:
                                    st.text(f"📄 {source}")
                    
                    # Show processing time
                    st.caption(f"⏱️ Response generated in {response.processing_time:.2f}s")
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
        
def main():
    """Main application entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "streamlit":
            if not STREAMLIT_AVAILABLE:
                print("Streamlit is not installed. Please install it with: pip install streamlit")
                print("Or run the API server with: python app_refactored.py api")
                return
            create_streamlit_app()
        elif sys.argv[1] == "api":
            import uvicorn
            logger.info(f"🚀 Starting FastAPI server on {config.api_host}:{config.api_port}...")
            uvicorn.run(app, host=config.api_host, port=config.api_port)
        else:
            print_usage()
    else:
        # Default behavior - check what's available
        if STREAMLIT_AVAILABLE:
            create_streamlit_app()
        else:
            print("Streamlit not available. Starting API server instead...")
            print(f"Access the API at: {config.api_url}")
            print(f"API docs at: {config.api_url}/docs")
            import uvicorn
            uvicorn.run(app, host=config.api_host, port=config.api_port)

if __name__ == "__main__":
    main()