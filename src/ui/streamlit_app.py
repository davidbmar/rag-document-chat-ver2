#!/usr/bin/env python3
"""
Streamlit app for RAG Document Chat System
"""

import asyncio
import os
import logging
import streamlit as st

# Don't force demo mode - let config determine based on API key availability

from src.search.rag_system import RAGSystem

# Set up logging for button clicks
logger = logging.getLogger(__name__)

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
            logger.info(f"📄 BUTTON CLICKED: Basic Chunks for file: {uploaded_file.name}")
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
                logger.info(f"🧠 BUTTON CLICKED: Smart Summaries for file: {uploaded_file.name}")
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
                logger.info(f"📝 BUTTON CLICKED: Paragraph Context for file: {uploaded_file.name}")
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
    
    # Add comprehensive document status panel
    st.divider()
    st.subheader("📊 Document Inventory & Status")
    
    def get_comprehensive_document_status():
        """Get detailed status of all indexed documents and collections"""
        status_data = {
            'collections': {},
            'documents_by_file': {},
            'total_items': 0,
            'errors': []
        }
        
        try:
            # Get all collections
            all_collections = rag_system.clients.chromadb.client.list_collections()
            
            for collection_info in all_collections:
                collection_name = collection_info.name
                try:
                    # Get collection data
                    collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                    items = collection.get()
                    
                    count = len(items.get('ids', []))
                    status_data['total_items'] += count
                    
                    # Analyze documents by filename
                    filenames = set()
                    if 'metadatas' in items and items['metadatas']:
                        for metadata in items['metadatas']:
                            if isinstance(metadata, dict) and 'filename' in metadata:
                                filename = metadata['filename']
                                filenames.add(filename)
                                
                                # Track by document
                                if filename not in status_data['documents_by_file']:
                                    status_data['documents_by_file'][filename] = {
                                        'collections': {},
                                        'total_items': 0
                                    }
                                
                                if collection_name not in status_data['documents_by_file'][filename]['collections']:
                                    status_data['documents_by_file'][filename]['collections'][collection_name] = 0
                                
                                status_data['documents_by_file'][filename]['collections'][collection_name] += 1
                                status_data['documents_by_file'][filename]['total_items'] += 1
                    
                    # Store collection summary
                    status_data['collections'][collection_name] = {
                        'count': count,
                        'filenames': list(filenames),
                        'sample_metadata': items.get('metadatas', [])[:2] if items.get('metadatas') else []
                    }
                    
                except Exception as e:
                    status_data['errors'].append(f"Error accessing {collection_name}: {str(e)}")
                    status_data['collections'][collection_name] = {'count': 'Error', 'filenames': [], 'sample_metadata': []}
        
        except Exception as e:
            status_data['errors'].append(f"Error listing collections: {str(e)}")
        
        return status_data
    
    # Get comprehensive status
    status = get_comprehensive_document_status()
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", status['total_items'])
    
    with col2:
        st.metric("Collections", len(status['collections']))
    
    with col3:
        st.metric("Unique Documents", len(status['documents_by_file']))
    
    with col4:
        if status['errors']:
            st.metric("Errors", len(status['errors']), delta="⚠️")
        else:
            st.metric("Status", "✅ OK")
    
    # Detailed breakdown
    if status['total_items'] > 0:
        
        # Show documents breakdown
        if status['documents_by_file']:
            st.subheader("📄 Documents Breakdown")
            for filename, doc_data in status['documents_by_file'].items():
                with st.expander(f"📄 {filename} ({doc_data['total_items']} items)"):
                    cols = st.columns(len(doc_data['collections']) if doc_data['collections'] else 1)
                    
                    for i, (collection_name, count) in enumerate(doc_data['collections'].items()):
                        with cols[i % len(cols)]:
                            st.metric(collection_name.replace('_', ' ').title(), count)
        
        # Show collections breakdown
        st.subheader("🗄️ Collections Breakdown")
        for collection_name, collection_data in status['collections'].items():
            if collection_data['count'] > 0:
                with st.expander(f"🗄️ {collection_name} ({collection_data['count']} items)"):
                    if collection_data['filenames']:
                        st.write("**Files:**", ", ".join(collection_data['filenames']))
                    
                    if collection_data['sample_metadata']:
                        st.write("**Sample Metadata:**")
                        for i, meta in enumerate(collection_data['sample_metadata']):
                            st.json(meta, expanded=False)
    
    else:
        st.info("📭 No documents are currently indexed. Upload a document to get started!")
    
    # Show any errors
    if status['errors']:
        st.error("⚠️ Errors encountered:")
        for error in status['errors']:
            st.write(f"• {error}")
    
    # Real-time collection monitoring (for debugging)
    with st.expander("🔧 Technical Details", expanded=False):
        st.write("**Raw Collection Data:**")
        
        # Show what ChromaDB actually contains
        try:
            collections_raw = rag_system.clients.chromadb.client.list_collections()
            for collection_info in collections_raw:
                collection_name = collection_info.name
                try:
                    collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                    items = collection.get()
                    
                    st.write(f"**{collection_name}:**")
                    st.write(f"  - Items: {len(items.get('ids', []))}")
                    st.write(f"  - IDs: {items.get('ids', [])[:3]}{'...' if len(items.get('ids', [])) > 3 else ''}")
                    
                    if items.get('metadatas'):
                        sample_filenames = [meta.get('filename', 'unknown') for meta in items['metadatas'][:3]]
                        st.write(f"  - Sample files: {sample_filenames}")
                
                except Exception as e:
                    st.write(f"**{collection_name}:** Error - {str(e)}")
                    
        except Exception as e:
            st.write(f"Error accessing raw data: {e}")
        
        # Show S3 status if available
        try:
            from src.core.config import config
            if hasattr(rag_system.clients, 's3') and rag_system.clients.s3 and config.s3_bucket:
                st.write("**S3 Storage:**")
                try:
                    s3_response = rag_system.clients.s3.list_objects_v2(Bucket=config.s3_bucket)
                    if 'Contents' in s3_response:
                        s3_files = [obj['Key'] for obj in s3_response['Contents']]
                        st.write(f"  - Files in S3: {len(s3_files)}")
                        st.write(f"  - Sample files: {s3_files[:5]}")
                    else:
                        st.write("  - S3 bucket is empty")
                except Exception as s3_e:
                    st.write(f"  - S3 error: {s3_e}")
            else:
                st.write("**S3 Storage:** Not configured or not available")
        except:
            pass


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
    logger.info("🗨️ BUTTON CLICKED: Clear Chat History")
    logger.info("ℹ️ NOTE: This only clears chat display and conversation memory - documents remain in database")
    
    st.session_state.messages = []
    st.session_state.conversation_history = []
    if 'last_processed_file' in st.session_state:
        del st.session_state['last_processed_file']
    
    logger.info("✅ Chat history and conversation memory cleared")
    st.success("💬 Chat history cleared!")
    st.info("ℹ️ Note: Processed documents remain in database. Use 'Clear Everything' to remove documents.")
    st.rerun()

def clear_everything():
    """Clear all data: chat, documents, vectors, S3 files using Docker volume reset approach"""
    try:
        logger.info("⚠️ BUTTON CLICKED: Clear Everything")
        logger.info("🚀 Starting COMPREHENSIVE Clear Everything operation...")
        st.info("🚀 Starting Clear Everything operation...")
        
        # Clear session data first
        st.session_state.messages = []
        st.session_state.conversation_history = []
        if 'last_processed_file' in st.session_state:
            del st.session_state['last_processed_file']
        
        st.info("✅ Step 1: Cleared session data")
        
        # Get current RAG system for S3 clearing
        rag_system = st.session_state.rag_system
        
        # STEP 1: Clear S3 data first
        st.info("☁️ Step 2: Clearing S3 storage...")
        try:
            if hasattr(rag_system.clients, 's3') and rag_system.clients.s3:
                from src.core.config import config
                if config.s3_bucket:
                    s3_client = rag_system.clients.s3
                    bucket = config.s3_bucket
                    
                    # List all objects
                    response = s3_client.list_objects_v2(Bucket=bucket)
                    if 'Contents' in response:
                        objects_found = response['Contents']
                        st.info(f"📋 Found {len(objects_found)} files in S3")
                        
                        # Delete all objects
                        objects_to_delete = [{'Key': obj['Key']} for obj in objects_found]
                        if objects_to_delete:
                            delete_response = s3_client.delete_objects(
                                Bucket=bucket,
                                Delete={'Objects': objects_to_delete}
                            )
                            
                            if 'Errors' in delete_response:
                                st.error(f"❌ S3 deletion errors: {delete_response['Errors']}")
                            else:
                                st.success(f"✅ Deleted {len(objects_to_delete)} files from S3")
                        else:
                            st.info("📁 S3 bucket was already empty")
                    else:
                        st.info("📁 S3 bucket was empty")
                else:
                    st.info("ℹ️ No S3 bucket configured")
            else:
                st.info("ℹ️ S3 client not available")
        except Exception as e:
            st.warning(f"⚠️ S3 clearing failed: {str(e)}")
        
        # STEP 2: Nuclear approach - Delete Docker volume and recreate ChromaDB
        st.info("💥 Step 3: Resetting ChromaDB with fresh storage...")
        
        try:
            import subprocess
            import time
            
            # Stop all services
            st.info("🛑 Stopping all services...")
            try:
                result = subprocess.run(
                    ["docker-compose", "down"], 
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    st.success("✅ Services stopped cleanly")
                else:
                    st.warning(f"⚠️ docker-compose down returned {result.returncode}: {result.stderr}")
            except Exception as e:
                st.warning(f"⚠️ Error stopping services: {e}")
                # Fallback - force stop ChromaDB container
                try:
                    subprocess.run(["docker", "stop", "rag_chromadb"], capture_output=True, timeout=10)
                    subprocess.run(["docker", "rm", "-f", "rag_chromadb"], capture_output=True, timeout=10)
                    st.info("✅ Force stopped ChromaDB container")
                except:
                    pass
            
            # Wait for cleanup
            time.sleep(3)
            
            # Delete the persistent volume
            st.info("🗑️ Deleting persistent ChromaDB volume...")
            try:
                volume_result = subprocess.run(
                    ["docker", "volume", "rm", "rag-document-chat-ver2_chromadb_data"], 
                    capture_output=True, text=True, timeout=30
                )
                if volume_result.returncode == 0:
                    st.success("✅ Persistent ChromaDB volume deleted!")
                else:
                    st.error(f"❌ Failed to delete volume: {volume_result.stderr}")
            except Exception as e:
                st.error(f"❌ Volume deletion failed: {e}")
            
            # Recreate ChromaDB with fresh volume
            st.info("🚀 Recreating ChromaDB with fresh storage...")
            try:
                recreate_result = subprocess.run(
                    ["docker-compose", "up", "-d", "chromadb"], 
                    capture_output=True, text=True, timeout=60
                )
                if recreate_result.returncode == 0:
                    st.success("✅ ChromaDB recreated with fresh storage")
                else:
                    st.error(f"❌ Failed to recreate ChromaDB: {recreate_result.stderr}")
            except Exception as e:
                st.error(f"❌ ChromaDB recreation failed: {e}")
            
            # Wait for ChromaDB to be ready
            st.info("⏳ Waiting for new ChromaDB to be ready...")
            for i in range(15):  # Wait up to 30 seconds
                try:
                    import requests
                    response = requests.get("http://localhost:8002/api/v2/heartbeat", timeout=2)
                    if response.status_code == 200:
                        st.success("✅ Fresh ChromaDB is ready!")
                        break
                except:
                    time.sleep(2)
            else:
                st.warning("⚠️ ChromaDB may not be ready - check manually")
            
        except Exception as e:
            st.error(f"❌ Docker operations failed: {e}")
        
        # STEP 3: Complete session reset
        st.info("🔄 Step 4: Reinitializing system...")
        try:
            # Clear all session state
            session_keys = list(st.session_state.keys())
            for key in session_keys:
                del st.session_state[key]
            
            # Create fresh RAG system
            from src.search.rag_system import RAGSystem
            st.session_state.rag_system = RAGSystem()
            st.session_state.messages = []
            st.session_state.conversation_history = []
            
            st.success("✅ System reinitialized with fresh state")
            
        except Exception as e:
            st.error(f"❌ System reinitialization failed: {e}")
        
        # STEP 4: Verification
        st.info("🔍 Step 5: Verifying clean state...")
        try:
            # Check if collections exist
            new_rag = st.session_state.rag_system
            collections = new_rag.clients.chromadb.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if collection_names:
                st.warning(f"⚠️ Some collections exist: {collection_names}")
                # Check if they have data
                total_items = 0
                for name in collection_names:
                    try:
                        coll = new_rag.clients.chromadb.get_collection(name)
                        count = len(coll.get()['ids'])
                        total_items += count
                        st.info(f"📊 Collection '{name}': {count} items")
                    except:
                        pass
                
                if total_items == 0:
                    st.success("✅ All collections are empty - CLEAN STATE ACHIEVED!")
                else:
                    st.error(f"❌ Found {total_items} items across collections after reset!")
            else:
                st.success("✅ No collections exist - PERFECT CLEAN STATE!")
                
        except Exception as e:
            st.warning(f"⚠️ Could not verify state: {e}")
        
        st.success("🎉 Clear Everything operation completed!")
        st.info("🔄 Page will refresh automatically...")
        
        # Force page refresh
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.reload();
        }, 2000);
        </script>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error during clear operation: {str(e)}")
        logger.error(f"Clear Everything failed: {str(e)}")
        st.code(f"Error details: {str(e)}")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources for assistant messages
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("📚 Sources", expanded=False):
                for source in message["sources"]:
                    st.text(f"• {source}")
        
        # Show raw citations for assistant messages
        if message["role"] == "assistant" and "raw_citations" in message and message["raw_citations"]:
            with st.expander(f"📖 Raw Citations ({len(message['raw_citations'])} excerpts)", expanded=False):
                for i, citation in enumerate(message["raw_citations"], 1):
                    st.markdown(f"**Citation {i}:** {citation.get('document', 'unknown')} ({citation.get('collection', 'unknown')})")
                    
                    # Display the citation text in a clean format
                    citation_text = citation.get('text', 'No text available')
                    st.markdown(f"> {citation_text}")
                    
                    # Show additional context if available
                    if citation.get('context'):
                        st.caption(f"Context: {citation['context']}")
                    
                    if i < len(message["raw_citations"]):  # Don't add divider after last citation
                        st.divider()

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
                
                # COMPREHENSIVE DEBUG: Check ALL possible data sources
                try:
                    chromadb_client = rag_system.clients.chromadb
                    debug_info = []
                    total_items = 0
                    
                    # Check if we're using the SAME ChromaDB client instance
                    st.caption(f"🔍 CLIENT DEBUG: ChromaDB client ID: {id(chromadb_client)}")
                    st.caption(f"🔍 CLIENT DEBUG: SearchEngine client ID: {id(rag_system.search_engine.clients.chromadb)}")
                    
                    # Check all possible collection names that might exist
                    all_possible_collections = ["documents", "logical_summaries", "paragraph_summaries", "original_texts"]
                    
                    # First, list ALL collections that actually exist in ChromaDB
                    try:
                        # Use the underlying client to list collections
                        all_collections = chromadb_client.client.list_collections()
                        existing_collection_names = [col.name for col in all_collections]
                        st.caption(f"🔍 ALL COLLECTIONS: {existing_collection_names}")
                        
                        # Add any unknown collections to our check list
                        for name in existing_collection_names:
                            if name not in all_possible_collections:
                                all_possible_collections.append(name)
                                
                    except Exception as e:
                        st.caption(f"🔍 LIST COLLECTIONS ERROR: {e}")
                    
                    # Now check each collection thoroughly
                    for coll_name in all_possible_collections:
                        try:
                            coll = chromadb_client.get_collection(coll_name)
                            items = coll.get()
                            count = len(items['ids']) if items and 'ids' in items else 0
                            debug_info.append(f"{coll_name}:{count}")
                            total_items += count
                            
                            # Show sample IDs and metadata if any exist
                            if count > 0 and items['ids']:
                                sample_ids = items['ids'][:3]  # First 3 IDs
                                debug_info.append(f"  └─ IDs: {sample_ids}")
                                
                                # Show metadata to see where data comes from
                                if 'metadatas' in items and items['metadatas']:
                                    sample_meta = items['metadatas'][:2]
                                    debug_info.append(f"  └─ Meta: {sample_meta}")
                                
                                # Look for alice.txt specifically
                                alice_count = 0
                                for meta in items['metadatas']:
                                    if 'filename' in meta and 'alice' in meta['filename'].lower():
                                        alice_count += 1
                                if alice_count > 0:
                                    debug_info.append(f"  └─ ⚠️ ALICE DATA FOUND: {alice_count} items!")
                                
                                # Show sample documents
                                if 'documents' in items and items['documents']:
                                    sample_docs = [doc[:50] + "..." if len(doc) > 50 else doc for doc in items['documents'][:2]]
                                    debug_info.append(f"  └─ Docs: {sample_docs}")
                                
                        except Exception as e:
                            if "does not exist" not in str(e).lower():
                                debug_info.append(f"{coll_name}:ERROR({str(e)[:30]})")
                    
                    # Also check the SearchEngine's collection references directly
                    try:
                        se_doc_count = len(rag_system.search_engine.document_collection.get()['ids'])
                        se_sum_count = len(rag_system.search_engine.summary_collection.get()['ids']) 
                        se_par_count = len(rag_system.search_engine.paragraph_collection.get()['ids'])
                        
                        debug_info.append(f"SearchEngine.document_collection:{se_doc_count}")
                        debug_info.append(f"SearchEngine.summary_collection:{se_sum_count}")  
                        debug_info.append(f"SearchEngine.paragraph_collection:{se_par_count}")
                        
                        total_items += se_doc_count + se_sum_count + se_par_count
                        
                    except Exception as e:
                        debug_info.append(f"SearchEngine collections:ERROR({str(e)[:30]})")
                    
                    st.caption(f"🔍 DEBUG: Total items across all collections: {total_items}")
                    st.caption(f"🔍 DEBUG: {chr(10).join(debug_info)}")
                    
                    # CRITICAL: Test if we can actually search and find alice data
                    try:
                        test_embedding = rag_system.clients.openai.get_embedding("alice")
                        test_results = rag_system.search_engine.document_collection.query(
                            query_embeddings=[test_embedding],
                            n_results=3
                        )
                        
                        if test_results['documents'][0]:
                            st.caption(f"🔍 SEARCH TEST: Found {len(test_results['documents'][0])} results for 'alice'")
                            if test_results['metadatas'][0]:
                                alice_files = [meta.get('filename', 'unknown') for meta in test_results['metadatas'][0]]
                                st.caption(f"🔍 SEARCH TEST: Files found: {alice_files}")
                        else:
                            st.caption("🔍 SEARCH TEST: No results found for 'alice'")
                            
                    except Exception as e:
                        st.caption(f"🔍 SEARCH TEST ERROR: {e}")
                    
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
                    "sources": response.sources,
                    "raw_citations": getattr(response, 'raw_citations', [])
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
                
                # Show raw citations
                if hasattr(response, 'raw_citations') and response.raw_citations:
                    with st.expander(f"📖 Raw Citations ({len(response.raw_citations)} excerpts)", expanded=False):
                        for i, citation in enumerate(response.raw_citations, 1):
                            st.markdown(f"**Citation {i}:** {citation.document} ({citation.collection})")
                            
                            # Display the citation text in a clean format
                            st.markdown(f"> {citation.text}")
                            
                            # Show additional context if available
                            if citation.context:
                                st.caption(f"Context: {citation.context}")
                            
                            # Add copy button for the citation text
                            if st.button(f"📋 Copy Citation {i}", key=f"copy_citation_{i}"):
                                st.code(citation.text)
                                st.success("Citation copied to view!")
                            
                            if i < len(response.raw_citations):  # Don't add divider after last citation
                                st.divider()
                
                # Show processing time
                st.caption(f"⏱️ Response generated in {response.processing_time:.2f}s")
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": [],
                    "raw_citations": []
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
    
    from src.core.config import config
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
        if st.button("🗨️ Clear Chat Only", use_container_width=True, help="Clear conversation display and memory only (documents remain in database)"):
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
        "⚠️ Clear All Documents & Chat", 
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