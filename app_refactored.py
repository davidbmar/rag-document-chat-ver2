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

from config import config
from models import ChatRequest, ChatResponse, DocumentResponse
from rag_system import RAGSystem
from utils import print_usage, setup_logging

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
            logger.info("🚀 Starting FastAPI server...")
            uvicorn.run(app, host="0.0.0.0", port=8001)
        else:
            print_usage()
    else:
        # Default behavior - check what's available
        if STREAMLIT_AVAILABLE:
            create_streamlit_app()
        else:
            print("Streamlit not available. Starting API server instead...")
            print("Access the API at: http://localhost:8001")
            print("API docs at: http://localhost:8001/docs")
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()