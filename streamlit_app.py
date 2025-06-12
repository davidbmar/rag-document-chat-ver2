#!/usr/bin/env python3
"""
Streamlit app for RAG Document Chat System
"""

import asyncio
import os
import streamlit as st

# Don't force demo mode - let config determine based on API key availability

from rag_system import RAGSystem

# Initialize RAG system
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem()

rag_system = st.session_state.rag_system

# Streamlit Interface
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
    col1, col2, col3 = st.columns(3)
    
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
    
    # Step 3: Paragraph Processing (only available after step 1)
    with col3:
        if 'last_processed_file' in st.session_state and st.session_state['last_processed_file'] == uploaded_file.name:
            if st.button("📝 Paragraph Context", use_container_width=True, help="Create paragraph summaries for wider search context"):
                with st.spinner("Creating paragraph summaries (3:1 compression)..."):
                    try:
                        result = asyncio.run(
                            rag_system.process_document_paragraphs(
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
                                    "Paragraphs", 
                                    result.paragraphs_processed
                                )
                            
                            with col_b:
                                st.metric(
                                    "Compression", 
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
                            
                            st.info(f"📄 Processed {input_words:,} words → {output_words:,} words in paragraph summaries")
                            
                        else:
                            st.error(f"❌ {result.message}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.button("📝 Paragraph Context", use_container_width=True, disabled=True, help="Process basic chunks first")
    
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
        
        paragraph_count = 0
        try:
            paragraph_collection = rag_system.clients.chromadb.get_or_create_collection("paragraph_summaries")
            paragraph_count = len(paragraph_collection.get()['ids'])
        except:
            paragraph_count = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Basic Chunks", basic_count)
        with col2:
            st.metric("Smart Summaries", summary_count)
        with col3:
            st.metric("Paragraph Summaries", paragraph_count)
            
    except Exception as e:
        st.warning("Could not retrieve processing stats")


# Main chat interface
st.header("💬 Chat with Your Documents")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize conversation history for context (last 15 messages)
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

def add_to_conversation_history(user_message: str, assistant_response: str):
    """Add a conversation turn to history, maintaining max 15 messages (7-8 turns)"""
    st.session_state.conversation_history.append({
        "user": user_message,
        "assistant": assistant_response
    })
    
    # Keep only last 15 messages (roughly 7-8 conversation turns)
    if len(st.session_state.conversation_history) > 7:
        st.session_state.conversation_history = st.session_state.conversation_history[-7:]

def get_conversation_context() -> str:
    """Format conversation history for inclusion in context"""
    if not st.session_state.conversation_history:
        return ""
    
    context_parts = []
    for i, turn in enumerate(st.session_state.conversation_history, 1):
        context_parts.append(f"Previous Q{i}: {turn['user']}")
        context_parts.append(f"Previous A{i}: {turn['assistant']}")
    
    return "\n".join(context_parts)

def clear_chat_history():
    """Clear only chat display and conversation memory"""
    st.session_state.messages = []
    st.session_state.conversation_history = []
    if 'last_processed_file' in st.session_state:
        del st.session_state['last_processed_file']
    st.success("💬 Chat history cleared!")
    st.rerun()

def clear_everything():
    """Clear all data: chat, documents, vectors, S3 files"""
    try:
        st.info("🚀 Starting Clear Everything operation...")
        
        # Clear session data
        st.session_state.messages = []
        st.session_state.conversation_history = []
        if 'last_processed_file' in st.session_state:
            del st.session_state['last_processed_file']
        
        st.info("🧹 Cleared session data")
        
        # Clear ChromaDB collections
        rag_system = st.session_state.rag_system
        chromadb_client = rag_system.clients.chromadb
        
        collections_to_delete = [
            "documents", 
            "logical_summaries", 
            "paragraph_summaries",
            "original_texts"  # Found this in the logs!
        ]
        
        # The problem: SearchEngine uses get_or_create_collection() which recreates them!
        # Solution: Delete collections AND clear all data from recreated ones
        deleted_count = 0
        cleared_count = 0
        
        for collection_name in collections_to_delete:
            try:
                # First, try to delete the collection completely
                try:
                    collection = chromadb_client.get_collection(collection_name)
                    items = collection.get()
                    count = len(items['ids']) if items and 'ids' in items else 0
                    
                    if count > 0:
                        st.info(f"📋 Found {collection_name} with {count} items")
                        st.code(f"Sample IDs: {items['ids'][:3] if items['ids'] else 'None'}")
                        
                        # Actually delete the collection
                        chromadb_client.delete_collection(collection_name)
                        st.success(f"🗑️ Deleted {collection_name} collection")
                        deleted_count += 1
                        
                        # Verify deletion worked
                        try:
                            chromadb_client.get_collection(collection_name)
                            st.error(f"❌ {collection_name} still exists after deletion!")
                        except:
                            st.success(f"✅ {collection_name} successfully deleted")
                            
                    else:
                        st.info(f"📭 Collection {collection_name} was already empty")
                        
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        st.info(f"ℹ️ Collection {collection_name} didn't exist")
                    else:
                        st.warning(f"⚠️ Could not delete {collection_name}: {str(e)}")
                        st.code(f"Error details: {str(e)}")
                
                # Now, since SearchEngine will recreate it, get the new empty one and verify it's empty
                try:
                    new_collection = chromadb_client.get_or_create_collection(collection_name)
                    new_items = new_collection.get()
                    remaining_count = len(new_items['ids']) if new_items and 'ids' in new_items else 0
                    
                    if remaining_count == 0:
                        st.success(f"✅ {collection_name} is now empty")
                        cleared_count += 1
                    else:
                        st.error(f"❌ {collection_name} still has {remaining_count} items!")
                        st.code(f"Remaining IDs: {new_items['ids'][:3] if new_items and new_items['ids'] else 'None'}")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not verify {collection_name}: {str(e)}")
                    st.code(f"Verification error: {str(e)}")
                    
            except Exception as e:
                st.error(f"❌ Failed to process {collection_name}: {str(e)}")
        
        if deleted_count > 0 or cleared_count > 0:
            st.success(f"🧹 Processed {deleted_count + cleared_count} ChromaDB collections")
        else:
            st.info("📭 No ChromaDB collections to process")
        
        # Clear S3 files (if configured)
        try:
            if hasattr(rag_system.clients, 's3') and rag_system.clients.s3:
                from config import config
                if config.s3_bucket:
                    s3_client = rag_system.clients.s3
                    bucket = config.s3_bucket
                    
                    # List and delete all objects in bucket
                    response = s3_client.list_objects_v2(Bucket=bucket)
                    if 'Contents' in response:
                        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                        if objects_to_delete:
                            s3_client.delete_objects(
                                Bucket=bucket,
                                Delete={'Objects': objects_to_delete}
                            )
                            st.info(f"🗑️ Deleted {len(objects_to_delete)} files from S3")
                        else:
                            st.info("📁 S3 bucket was already empty")
                    else:
                        st.info("📁 S3 bucket was already empty")
        except Exception as e:
            st.warning(f"⚠️ Could not clear S3 files: {str(e)}")
        
        # Force reinitialize RAG system to clear collection references
        try:
            st.info("🔄 Reinitializing RAG system...")
            from rag_system import RAGSystem
            st.session_state.rag_system = RAGSystem()
            st.success("✅ RAG system reinitialized")
        except Exception as e:
            st.warning(f"⚠️ Could not reinitialize RAG system: {str(e)}")
        
        st.success("🧹 Everything cleared! System reset to fresh state.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during cleanup: {str(e)}")

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
                    summary_items = summary_collection.get()
                    summary_count = len(summary_items['ids']) if summary_items and 'ids' in summary_items else 0
                    has_summaries = summary_count > 0
                    st.caption(f"🔍 SUMMARY CHECK: {summary_count} items, has_summaries={has_summaries}")
                except Exception as e:
                    has_summaries = False
                    st.caption(f"🔍 SUMMARY CHECK: ERROR - {str(e)[:50]}")
                
                try:
                    paragraph_collection = rag_system.clients.chromadb.get_or_create_collection("paragraph_summaries")
                    paragraph_items = paragraph_collection.get()
                    paragraph_count = len(paragraph_items['ids']) if paragraph_items and 'ids' in paragraph_items else 0
                    has_paragraphs = paragraph_count > 0
                    st.caption(f"🔍 PARAGRAPH CHECK: {paragraph_count} items, has_paragraphs={has_paragraphs}")
                except Exception as e:
                    has_paragraphs = False
                    st.caption(f"🔍 PARAGRAPH CHECK: ERROR - {str(e)[:50]}")
                
                # Get conversation context for continuity
                conversation_context = get_conversation_context()
                
                # DEBUG: Check what collections actually exist and have data
                try:
                    chromadb_client = rag_system.clients.chromadb
                    debug_info = []
                    total_items = 0
                    
                    for coll_name in ["documents", "logical_summaries", "paragraph_summaries", "original_texts"]:
                        try:
                            coll = chromadb_client.get_collection(coll_name)
                            items = coll.get()
                            count = len(items['ids']) if items and 'ids' in items else 0
                            debug_info.append(f"{coll_name}:{count}")
                            total_items += count
                            
                            # Show sample IDs and metadata if any exist
                            if count > 0 and items['ids']:
                                sample_ids = items['ids'][:2]  # First 2 IDs
                                debug_info.append(f"  └─ IDs: {sample_ids}")
                                
                                # Show metadata to see where data comes from
                                if 'metadatas' in items and items['metadatas']:
                                    sample_meta = items['metadatas'][:2]
                                    debug_info.append(f"  └─ Meta: {sample_meta}")
                                
                                # Show sample documents
                                if 'documents' in items and items['documents']:
                                    sample_docs = [doc[:50] + "..." if len(doc) > 50 else doc for doc in items['documents'][:2]]
                                    debug_info.append(f"  └─ Docs: {sample_docs}")
                                
                        except Exception as e:
                            debug_info.append(f"{coll_name}:ERROR({str(e)[:30]})")
                    
                    st.caption(f"🔍 DEBUG: Total items across all collections: {total_items}")
                    st.caption(f"🔍 DEBUG: {chr(10).join(debug_info)}")
                    
                except Exception as e:
                    st.caption(f"🔍 DEBUG: Could not check collections: {e}")
                
                # CRITICAL DEBUG: Check which search path we're taking
                st.caption(f"🔍 SEARCH DEBUG: has_paragraphs={has_paragraphs}, has_summaries={has_summaries}")
                
                if has_paragraphs:
                    st.caption("🔍 TAKING PARAGRAPH SEARCH PATH")
                    response = rag_system.search_with_paragraphs(prompt, top_k_paragraphs=3, top_k_chunks=5, conversation_history=conversation_context)
                    st.caption("📝 Using paragraph context + detailed chunks + conversation history")
                elif has_summaries:
                    st.caption("🔍 TAKING ENHANCED SEARCH PATH")
                    response = rag_system.search_enhanced(prompt, top_k=8, use_summaries=True, conversation_history=conversation_context)
                    st.caption("🧠 Using smart summaries + detailed chunks + conversation history")
                else:
                    st.caption("🔍 TAKING BASIC SEARCH PATH")
                    response = rag_system.search_and_answer(prompt, top_k=8, conversation_history=conversation_context)
                    st.caption("📄 Using basic chunks + conversation history")
                
                # DEBUG: Show response details
                st.caption(f"🔍 RESPONSE DEBUG: Answer length={len(response.answer)}, Sources count={len(response.sources)}")
                if response.sources:
                    st.caption(f"🔍 SOURCE DEBUG: {response.sources}")
                
                # Display answer
                st.markdown(response.answer)
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources
                })
                
                # Add to conversation history for context
                add_to_conversation_history(prompt, response.answer)
                
                # Show sources
                if response.sources:
                    with st.expander("📚 Sources", expanded=False):
                        for source in response.sources:
                            if source.startswith("Paragraph:"):
                                st.markdown(f"📝 {source}")
                            elif source.startswith("Summary:"):
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
                
                # Add error to conversation history too
                add_to_conversation_history(prompt, error_msg)

# Sidebar with system status
with st.sidebar:
    st.header("System Status")
    status = rag_system.get_system_status()
    
    for service, state in status.items():
        if state == "connected":
            st.success(f"✅ {service.title()}: Connected")
        elif state == "error":
            st.error(f"❌ {service.title()}: Error")
        elif state == "disabled":
            st.info(f"ℹ️ {service.title()}: Disabled")
        else:
            st.warning(f"⚠️ {service.title()}: {state}")
    
    from config import config
    if config.demo_mode:
        st.info("🎭 Running in Demo Mode")
        st.markdown("To use with real OpenAI API, set your API key in environment variables.")
    else:
        st.success("🚀 Production Mode - OpenAI API Active")
        st.markdown("Using real OpenAI GPT models for responses.")
    
    # Show conversation history status
    st.divider()
    st.subheader("💭 Conversation Memory")
    
    history_count = len(st.session_state.conversation_history)
    if history_count > 0:
        st.success(f"📚 {history_count} conversation turns stored")
        st.caption("Last 7 turns kept for context")
        
        with st.expander("View History", expanded=False):
            for i, turn in enumerate(st.session_state.conversation_history, 1):
                st.text(f"Q{i}: {turn['user'][:50]}...")
                st.text(f"A{i}: {turn['assistant'][:50]}...")
                st.divider()
        
        # Clear Chat button
        if st.button("🗨️ Clear Chat History", use_container_width=True, help="Clear conversation display and memory only"):
            clear_chat_history()
    else:
        st.info("💭 No conversation history yet")
        st.caption("Start chatting to build context")
    
    # Clear Everything section
    st.divider()
    st.subheader("🗑️ System Reset")
    
    # Debug info - show current collections
    try:
        rag_system = st.session_state.rag_system
        chromadb_client = rag_system.clients.chromadb
        
        # Check which collections exist by trying to get them
        collections_to_check = ["documents", "logical_summaries", "paragraph_summaries", "original_texts"]
        existing_collections = []
        
        for collection_name in collections_to_check:
            try:
                collection = chromadb_client.get_collection(collection_name)
                # If we can get it, it exists - check if it has data
                count = len(collection.get()['ids'])
                existing_collections.append(f"{collection_name}({count})")
            except:
                # Collection doesn't exist, skip
                pass
        
        if existing_collections:
            st.caption(f"🗄️ Current collections: {', '.join(existing_collections)}")
        else:
            st.caption("📭 No collections exist")
    except Exception as e:
        st.caption(f"⚠️ Could not check collections: {str(e)}")
    
    if st.button(
        "⚠️ Clear Everything", 
        use_container_width=True, 
        type="secondary",
        help="⚠️ WARNING: Deletes ALL data including:\n• Chat history & conversation memory\n• All processed documents\n• ChromaDB vectors & summaries\n• S3 uploaded files\n• All processing status\n\nThis cannot be undone!"
    ):
        # Warning dialog
        st.warning("🚨 **DANGER ZONE** 🚨")
        st.markdown("""
        **This will permanently delete:**
        - 💬 All chat history and conversation memory
        - 📚 All processed documents and their chunks
        - 🧠 All smart summaries and paragraph summaries  
        - 🗄️ All ChromaDB vector collections
        - ☁️ All uploaded files from S3 storage
        - ⚙️ All processing status and session data
        
        **This action cannot be undone!**
        """)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔥 Yes, Delete Everything", type="primary", use_container_width=True):
                clear_everything()