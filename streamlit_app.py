#!/usr/bin/env python3
"""
Streamlit app for RAG Document Chat System
"""

import asyncio
import os
import logging
import streamlit as st

# Don't force demo mode - let config determine based on API key availability

from rag_system import RAGSystem

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
    """Clear all data: chat, documents, vectors, S3 files"""
    try:
        logger.info("⚠️ BUTTON CLICKED: Clear Everything")
        logger.info("🚀 Starting COMPREHENSIVE Clear Everything operation...")
        st.info("🚀 Starting COMPREHENSIVE Clear Everything operation with EXTENSIVE DEBUGGING...")
        
        # Clear session data
        st.session_state.messages = []
        st.session_state.conversation_history = []
        if 'last_processed_file' in st.session_state:
            del st.session_state['last_processed_file']
        
        st.info("🧹 Cleared session data")
        
        # Get current RAG system and clients
        rag_system = st.session_state.rag_system
        chromadb_client = rag_system.clients.chromadb
        
        # STEP 1: List ALL collections that exist with detailed inspection
        st.info("🔍 Step 1: Discovering all existing collections with detailed inspection...")
        all_existing_collections = []
        try:
            # Use the underlying ChromaDB client to list collections
            collections = chromadb_client.client.list_collections()
            all_existing_collections = [col.name for col in collections]
            st.info(f"📋 Found collections: {all_existing_collections}")
            
            # DETAILED INSPECTION: Check each collection's content BEFORE deletion
            st.info("🔍 DETAILED INSPECTION BEFORE DELETION:")
            for col_name in all_existing_collections:
                try:
                    collection = chromadb_client.get_or_create_collection(col_name)
                    items = collection.get()
                    count = len(items['ids']) if items and 'ids' in items else 0
                    
                    st.info(f"📊 BEFORE: Collection '{col_name}' has {count} items")
                    
                    if count > 0 and 'alice' in col_name.lower():
                        st.warning(f"⚠️ ALICE DATA DETECTED in '{col_name}' with {count} items!")
                        
                    # Show sample metadata for logical_summaries specifically
                    if col_name == "logical_summaries" and count > 0:
                        sample_meta = items.get('metadatas', [])[:3]
                        st.info(f"🔍 logical_summaries metadata sample: {sample_meta}")
                        
                except Exception as e:
                    st.info(f"ℹ️ Could not inspect '{col_name}': {e}")
                    
        except Exception as e:
            st.error(f"❌ Could not list collections: {e}")
            # Fallback to known collection names
            all_existing_collections = ["documents", "logical_summaries", "paragraph_summaries", "original_texts"]
        
        # STEP 2: Delete ALL collections completely (not just their contents)
        st.info("🗑️ Step 2: Deleting ALL collections completely...")
        deleted_collections = []
        
        for collection_name in all_existing_collections:
            try:
                st.info(f"🎯 PROCESSING COLLECTION: '{collection_name}'")
                
                # Get collection info first using our wrapper
                try:
                    collection = chromadb_client.get_or_create_collection(collection_name)
                    items = collection.get()
                    count = len(items['ids']) if items and 'ids' in items else 0
                    st.info(f"🗑️ Found collection '{collection_name}' with {count} items")
                    
                    # Special attention to logical_summaries
                    if collection_name == "logical_summaries" and count > 0:
                        st.warning(f"🎯 TARGETING logical_summaries with {count} items - THIS IS WHERE ALICE DATA LIVES!")
                        
                except Exception as e:
                    st.info(f"ℹ️ Collection '{collection_name}' doesn't exist or can't be accessed: {e}")
                    continue
                
                # Delete the entire collection using the underlying client
                st.info(f"🗑️ ATTEMPTING TO DELETE '{collection_name}' using client.delete_collection()...")
                try:
                    # STEP 1: Try to delete via underlying client
                    chromadb_client.client.delete_collection(collection_name)
                    st.success(f"✅ Successfully called client.delete_collection('{collection_name}')")
                    
                    # STEP 2: Verify it's gone from underlying client
                    try:
                        remaining_collections = chromadb_client.client.list_collections()
                        remaining_names = [col.name for col in remaining_collections]
                        if collection_name in remaining_names:
                            st.error(f"❌ CRITICAL: '{collection_name}' still exists in ChromaDB after deletion!")
                        else:
                            st.success(f"✅ VERIFIED: '{collection_name}' removed from ChromaDB")
                    except Exception as verify_e:
                        st.warning(f"⚠️ Could not verify deletion: {verify_e}")
                    
                    # STEP 3: Clear wrapper cache
                    if collection_name in chromadb_client.collections:
                        del chromadb_client.collections[collection_name]
                        st.success(f"✅ Removed '{collection_name}' from wrapper cache")
                    
                    # STEP 4: Clear SearchEngine cached references
                    if hasattr(rag_system, 'search_engine'):
                        if collection_name == "documents":
                            old_ref = rag_system.search_engine.document_collection
                            rag_system.search_engine.document_collection = None
                            st.success(f"✅ Cleared SearchEngine.document_collection (was: {type(old_ref)})")
                        elif collection_name == "logical_summaries":
                            old_ref = rag_system.search_engine.summary_collection
                            rag_system.search_engine.summary_collection = None
                            st.success(f"✅ Cleared SearchEngine.summary_collection (was: {type(old_ref)})")
                        elif collection_name == "paragraph_summaries":
                            old_ref = rag_system.search_engine.paragraph_collection
                            rag_system.search_engine.paragraph_collection = None
                            st.success(f"✅ Cleared SearchEngine.paragraph_collection (was: {type(old_ref)})")
                    
                    deleted_collections.append(collection_name)
                    st.success(f"🎉 COMPLETED DELETION OF '{collection_name}' ({count} items)")
                        
                except Exception as e:
                    st.error(f"❌ CRITICAL FAILURE: Could not delete collection '{collection_name}': {e}")
                    st.error(f"❌ Exception type: {type(e)}")
                    st.error(f"❌ Exception details: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Failed to process collection '{collection_name}': {e}")
        
        # STEP 3: Extensive verification that collections are gone
        st.info("✅ Step 3: EXTENSIVE VERIFICATION that collections are deleted...")
        try:
            remaining_collections = chromadb_client.client.list_collections()
            remaining_names = [col.name for col in remaining_collections]
            
            st.info(f"🔍 Collections remaining after deletion: {remaining_names}")
            
            if remaining_names:
                st.error(f"❌ CRITICAL: Some collections still exist: {remaining_names}")
                
                # Check if logical_summaries specifically still exists
                if "logical_summaries" in remaining_names:
                    st.error("🚨 CRITICAL: logical_summaries collection STILL EXISTS after deletion!")
                    try:
                        # Try to access it and see what's in it
                        surviving_collection = chromadb_client.get_or_create_collection("logical_summaries")
                        surviving_items = surviving_collection.get()
                        surviving_count = len(surviving_items['ids']) if surviving_items and 'ids' in surviving_items else 0
                        st.error(f"🚨 logical_summaries still has {surviving_count} items!")
                    except Exception as check_e:
                        st.info(f"ℹ️ Could not check surviving logical_summaries: {check_e}")
            else:
                st.success("✅ All collections successfully deleted - CLEAN STATE ACHIEVED!")
        except Exception as e:
            st.error(f"❌ Could not verify deletion: {e}")
        
        # STEP 4: NUCLEAR OPTION - Delete Docker volume and recreate ChromaDB
        st.info("💥 Step 4: NUCLEAR OPTION - Destroying persistent ChromaDB storage...")
        
        try:
            import subprocess
            import time
            
            # STEP 1: Use docker-compose down to cleanly stop all services
            st.info("🛑 Stopping all services with docker-compose down...")
            try:
                down_result = subprocess.run(
                    ["docker-compose", "down"], 
                    capture_output=True, text=True, check=True
                )
                st.success("✅ All services stopped cleanly")
                st.info(f"docker-compose down output: {down_result.stdout}")
            except Exception as down_e:
                st.warning(f"⚠️ docker-compose down failed: {down_e}")
                # Fallback to manual container stop
                try:
                    subprocess.run(["docker", "stop", "rag_chromadb"], capture_output=True, text=True)
                    subprocess.run(["docker", "rm", "-f", "rag_chromadb"], capture_output=True, text=True)
                    st.info("✅ Fallback container cleanup completed")
                except:
                    pass
            
            # STEP 2: Wait a moment for complete cleanup
            st.info("⏳ Waiting for complete cleanup...")
            time.sleep(2)
            
            # STEP 3: Delete the persistent Docker volume
            st.info("💥 DELETING PERSISTENT CHROMADB VOLUME...")
            try:
                volume_result = subprocess.run(
                    ["docker", "volume", "rm", "rag-document-chat-ver2_chromadb_data"], 
                    check=True, capture_output=True, text=True
                )
                st.success("✅ PERSISTENT CHROMADB VOLUME DELETED!")
                st.info(f"Volume deletion output: {volume_result.stdout}")
            except Exception as vol_e:
                st.error(f"❌ CRITICAL: Could not delete ChromaDB volume: {vol_e}")
                st.error(f"Error details: {vol_e}")
                
                # Show what volumes exist
                try:
                    ls_result = subprocess.run(
                        ["docker", "volume", "ls"], capture_output=True, text=True
                    )
                    st.info(f"Available volumes: {ls_result.stdout}")
                except:
                    pass
            
            # STEP 4: Recreate ChromaDB with fresh volume
            st.info("🚀 Recreating ChromaDB with fresh storage...")
            recreate_result = subprocess.run(
                ["docker-compose", "up", "-d", "chromadb"], 
                check=True, capture_output=True, text=True
            )
            st.success("✅ ChromaDB recreated with fresh storage")
            st.info(f"Recreate output: {recreate_result.stdout}")
            
            # Wait for it to be ready
            st.info("⏳ Waiting for new ChromaDB to be ready...")
            for i in range(20):  # Wait up to 40 seconds
                try:
                    # Test ChromaDB connectivity
                    import requests
                    response = requests.get("http://localhost:8002/api/v2/heartbeat", timeout=2)
                    if response.status_code == 200:
                        st.success("✅ Fresh ChromaDB is ready!")
                        break
                except:
                    time.sleep(2)
                    
            if i == 19:  # If we went through all attempts
                st.error("❌ ChromaDB may not be ready - check manually")
            
        except Exception as docker_e:
            st.error(f"❌ Docker operations failed: {docker_e}")
            st.error(f"❌ Docker error details: {str(docker_e)}")
        
        # STEP 5: EXTENSIVE S3 INVESTIGATION AND CLEARING
        st.info("☁️ Step 5: EXTENSIVE S3 INVESTIGATION AND CLEARING...")
        try:
            if hasattr(rag_system.clients, 's3') and rag_system.clients.s3:
                from config import config
                if config.s3_bucket:
                    s3_client = rag_system.clients.s3
                    bucket = config.s3_bucket
                    
                    st.info(f"🔍 S3 INVESTIGATION: Checking bucket '{bucket}'...")
                    
                    # List and examine all objects in bucket
                    response = s3_client.list_objects_v2(Bucket=bucket)
                    if 'Contents' in response:
                        objects_found = response['Contents']
                        st.info(f"📋 S3 BEFORE CLEARING: Found {len(objects_found)} objects in bucket")
                        
                        # Check for alice-related files
                        alice_objects = [obj for obj in objects_found if 'alice' in obj['Key'].lower()]
                        if alice_objects:
                            st.warning(f"⚠️ ALICE FILES IN S3: Found {len(alice_objects)} alice-related files:")
                            for obj in alice_objects[:5]:  # Show first 5
                                st.info(f"   📄 S3 File: {obj['Key']} (Size: {obj['Size']} bytes)")
                        
                        # Delete all objects
                        objects_to_delete = [{'Key': obj['Key']} for obj in objects_found]
                        if objects_to_delete:
                            delete_response = s3_client.delete_objects(
                                Bucket=bucket,
                                Delete={'Objects': objects_to_delete}
                            )
                            
                            # Check for errors in deletion
                            if 'Errors' in delete_response:
                                st.error(f"❌ S3 DELETION ERRORS: {delete_response['Errors']}")
                            
                            st.success(f"🗑️ Deleted {len(objects_to_delete)} files from S3")
                            
                            # Verify S3 is empty
                            verify_response = s3_client.list_objects_v2(Bucket=bucket)
                            if 'Contents' in verify_response:
                                remaining_objects = verify_response['Contents']
                                st.error(f"❌ S3 STILL HAS FILES: {len(remaining_objects)} objects remain after deletion!")
                                for obj in remaining_objects[:3]:
                                    st.error(f"   📄 Remaining: {obj['Key']}")
                            else:
                                st.success("✅ S3 bucket verified empty")
                        else:
                            st.info("📁 S3 bucket was already empty")
                    else:
                        st.info("📁 S3 bucket was empty")
                else:
                    st.info("ℹ️ No S3 bucket configured")
            else:
                st.info("ℹ️ S3 client not available or not configured")
        except Exception as e:
            st.error(f"❌ S3 operation failed: {str(e)}")
            st.error(f"❌ S3 error details: {type(e)} - {str(e)}")
        
        # STEP 6: COMPLETE SESSION STATE RESET AND SYSTEM REINITIALIZATION
        st.info("🔄 Step 6: COMPLETE SESSION STATE RESET...")
        try:
            # CRITICAL: Clear ALL session state including messages
            st.info("🗑️ Clearing ALL session state...")
            session_keys_before = list(st.session_state.keys())
            st.info(f"Session keys before clearing: {session_keys_before}")
            
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("✅ ALL session state cleared")
            
            # Force reload ALL relevant modules to ensure fresh state
            st.info("🔄 Reloading Python modules...")
            import importlib
            import sys
            
            modules_to_reload = ['rag_system', 'search_engine', 'clients', 'models']
            for module_name in modules_to_reload:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    st.info(f"✅ Reloaded {module_name}")
            
            # Create completely fresh RAG system
            st.info("🆕 Creating fresh RAG system...")
            from rag_system import RAGSystem
            st.session_state.rag_system = RAGSystem()
            
            # Initialize fresh session state
            st.session_state.messages = []
            st.session_state.conversation_history = []
            
            # Verify the new system has fresh collections
            new_rag = st.session_state.rag_system
            doc_coll_id = id(new_rag.search_engine.document_collection)
            sum_coll_id = id(new_rag.search_engine.summary_collection)
            par_coll_id = id(new_rag.search_engine.paragraph_collection)
            
            st.success("✅ Fresh RAG system created with new collection objects")
            st.info(f"New collection object IDs: doc={doc_coll_id}, sum={sum_coll_id}, par={par_coll_id}")
            
        except Exception as e:
            st.error(f"❌ Could not reinitialize RAG system: {str(e)}")
            st.error(f"Error details: {type(e)} - {str(e)}")
        
        # STEP 7: FINAL COMPREHENSIVE VERIFICATION
        st.info("🔍 Step 7: FINAL COMPREHENSIVE VERIFICATION...")
        try:
            new_rag_system = st.session_state.rag_system
            new_chromadb_client = new_rag_system.clients.chromadb
            
            final_collections = new_chromadb_client.client.list_collections()
            final_names = [col.name for col in final_collections]
            
            st.info(f"🔍 FINAL STATE: Collections after full reset: {final_names}")
            
            if final_names:
                st.warning(f"⚠️ Some collections were recreated: {final_names}")
                
                # Detailed check of each recreated collection
                total_items = 0
                for name in final_names:
                    try:
                        coll = new_chromadb_client.get_or_create_collection(name)
                        items = coll.get()
                        count = len(items['ids']) if items and 'ids' in items else 0
                        total_items += count
                        
                        st.info(f"📊 FINAL: Collection '{name}': {count} items")
                        
                        # Critical check for alice data
                        if count > 0:
                            st.warning(f"⚠️ UNEXPECTED DATA: '{name}' has {count} items after full reset!")
                            
                            # Check metadata for alice references
                            if items.get('metadatas'):
                                sample_meta = items['metadatas'][:2]
                                st.info(f"🔍 FINAL METADATA in '{name}': {sample_meta}")
                                
                                # Look for alice filenames
                                alice_files = [meta.get('filename', '') for meta in items['metadatas'] if 'alice' in str(meta.get('filename', '')).lower()]
                                if alice_files:
                                    st.error(f"🚨 ALICE FILES DETECTED in '{name}': {alice_files}")
                    except Exception as coll_e:
                        st.info(f"ℹ️ Could not check collection '{name}': {coll_e}")
                        
                if total_items == 0:
                    st.success("✅ All recreated collections are empty - CLEAN STATE ACHIEVED!")
                else:
                    st.error(f"🚨 CRITICAL: {total_items} items found across collections after full reset!")
                    
            else:
                st.success("✅ No collections exist - PERFECT CLEAN STATE ACHIEVED!")
                
        except Exception as e:
            st.error(f"❌ Could not verify final state: {e}")
            st.error(f"❌ Final verification error details: {str(e)}")
        
        st.success("💥 COMPREHENSIVE CLEAR COMPLETE! System completely reset.")
        st.warning("🔄 IMPORTANT: You MUST refresh the browser page (F5) for the reset to take full effect!")
        st.info("The clear operation has completed, but Streamlit session state requires a page refresh.")
        
        # Force a complete page reload
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.reload();
        }, 3000);
        </script>
        """, unsafe_allow_html=True)
        
        st.info("⏳ Page will automatically refresh in 3 seconds...")
        
    except Exception as e:
        st.error(f"❌ Error during comprehensive cleanup: {str(e)}")
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