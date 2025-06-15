#!/usr/bin/env python3
"""
Complete Streamlit Workflow Test
Simulates the exact user workflow in Streamlit:
1. Upload file
2. Process Basic Chunks
3. Process Smart Summaries  
4. Process Paragraph Context
5. Query documents
6. Clear Everything
7. Query again to verify clear
"""

import asyncio
import time
import subprocess
import logging
from datetime import datetime
from rag_system import RAGSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class StreamlitWorkflowTest:
    def __init__(self):
        self.rag_system = None
        self.test_filename = "comprehensive_test.txt"
        
    def log_step(self, step: str, details: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{timestamp}] {step}")
        if details:
            logger.info(f"    {details}")
        print(f"🔄 [{timestamp}] {step}")
        if details:
            print(f"    {details}")

    def get_document_status(self):
        """Get current document status - simulates the new inventory panel"""
        try:
            collections = self.rag_system.clients.chromadb.client.list_collections()
            
            total_items = 0
            documents_by_file = {}
            collection_data = {}
            
            for collection_info in collections:
                collection_name = collection_info.name
                try:
                    collection = self.rag_system.clients.chromadb.get_or_create_collection(collection_name)
                    items = collection.get()
                    count = len(items.get('ids', []))
                    total_items += count
                    collection_data[collection_name] = count
                    
                    # Track by filename
                    if items.get('metadatas'):
                        for meta in items['metadatas']:
                            if isinstance(meta, dict) and 'filename' in meta:
                                filename = meta['filename']
                                if filename not in documents_by_file:
                                    documents_by_file[filename] = {}
                                documents_by_file[filename][collection_name] = documents_by_file[filename].get(collection_name, 0) + 1
                
                except Exception as e:
                    collection_data[collection_name] = f"Error: {e}"
            
            return {
                'total_items': total_items,
                'collections': collection_data,
                'documents': documents_by_file
            }
        except Exception as e:
            return {'error': str(e)}

    def print_status(self, title: str):
        """Print current status - simulates the document inventory panel"""
        print(f"\n📊 {title}")
        print("=" * 60)
        
        status = self.get_document_status()
        
        if 'error' in status:
            print(f"❌ Error: {status['error']}")
            return
        
        print(f"📈 Total Items: {status['total_items']}")
        print(f"📂 Collections: {len(status['collections'])}")
        print(f"📄 Unique Documents: {len(status['documents'])}")
        
        if status['documents']:
            print(f"\n📄 DOCUMENTS:")
            for filename, collections in status['documents'].items():
                total_for_file = sum(v for v in collections.values() if isinstance(v, int))
                print(f"   {filename}: {total_for_file} items")
                for coll_name, count in collections.items():
                    print(f"     └─ {coll_name}: {count}")
        
        if status['collections']:
            print(f"\n🗄️ COLLECTIONS:")
            for coll_name, count in status['collections'].items():
                print(f"   {coll_name}: {count}")
        
        print("=" * 60)

    def step_1_upload_and_basic_chunks(self):
        """Step 1: Upload file and process basic chunks (📄 Basic Chunks button)"""
        self.log_step("STEP 1: Upload and Process Basic Chunks", "Simulating file upload and Basic Chunks button click")
        
        try:
            # Initialize RAG system (simulates page load)
            self.rag_system = RAGSystem()
            
            # Read file content (simulates file upload)
            with open(self.test_filename, 'rb') as f:
                content = f.read()
            
            # Process document (simulates clicking "📄 Basic Chunks" button)
            result = asyncio.run(self.rag_system.process_document(content, self.test_filename))
            
            if result.status == "success":
                self.log_step("✅ Basic Chunks Processing SUCCESS", 
                             f"Processing time: {result.processing_time:.2f}s")
                self.print_status("STATUS AFTER BASIC CHUNKS")
                return True
            else:
                self.log_step("❌ Basic Chunks Processing FAILED", f"Error: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("❌ Basic Chunks Processing EXCEPTION", f"Error: {str(e)}")
            return False

    def step_2_smart_summaries(self):
        """Step 2: Process smart summaries (🧠 Smart Summaries button)"""
        self.log_step("STEP 2: Process Smart Summaries", "Simulating Smart Summaries button click")
        
        try:
            # Process hierarchically (simulates clicking "🧠 Smart Summaries" button)
            result = asyncio.run(self.rag_system.process_document_hierarchically(self.test_filename))
            
            if result.status == "success":
                compression_ratio = result.compression_stats.get('overall_compression_ratio', 0)
                self.log_step("✅ Smart Summaries Processing SUCCESS", 
                             f"Groups: {result.logical_groups_created}, Compression: {compression_ratio:.1f}:1")
                self.print_status("STATUS AFTER SMART SUMMARIES")
                return True
            else:
                self.log_step("❌ Smart Summaries Processing FAILED", f"Error: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("❌ Smart Summaries Processing EXCEPTION", f"Error: {str(e)}")
            return False

    def step_3_paragraph_context(self):
        """Step 3: Process paragraph context (📝 Paragraph Context button)"""
        self.log_step("STEP 3: Process Paragraph Context", "Simulating Paragraph Context button click")
        
        try:
            # Process paragraphs (simulates clicking "📝 Paragraph Context" button)
            result = asyncio.run(self.rag_system.process_document_paragraphs(self.test_filename))
            
            if result.status == "success":
                compression_ratio = result.compression_stats.get('overall_compression_ratio', 0)
                self.log_step("✅ Paragraph Context Processing SUCCESS", 
                             f"Paragraphs: {result.paragraphs_processed}, Compression: {compression_ratio:.1f}:1")
                self.print_status("STATUS AFTER PARAGRAPH CONTEXT")
                return True
            else:
                self.log_step("❌ Paragraph Context Processing FAILED", f"Error: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("❌ Paragraph Context Processing EXCEPTION", f"Error: {str(e)}")
            return False

    def step_4_query_documents(self, step_name: str):
        """Step 4: Query what documents are indexed (simulates chat input)"""
        self.log_step(f"STEP 4: {step_name}", "Querying: 'what documents have you indexed?'")
        
        try:
            query = "what documents have you indexed?"
            
            # Determine search method (simulates Streamlit logic)
            try:
                summary_collection = self.rag_system.clients.chromadb.get_or_create_collection("logical_summaries")
                summary_items = summary_collection.get()
                has_summaries = len(summary_items['ids']) > 0
            except:
                has_summaries = False
            
            try:
                paragraph_collection = self.rag_system.clients.chromadb.get_or_create_collection("paragraph_summaries")
                paragraph_items = paragraph_collection.get()
                has_paragraphs = len(paragraph_items['ids']) > 0
            except:
                has_paragraphs = False
            
            # Choose search method (matches Streamlit logic)
            if has_paragraphs:
                search_method = "paragraph_search"
                response = self.rag_system.search_with_paragraphs(query, top_k_paragraphs=3, top_k_chunks=5)
            elif has_summaries:
                search_method = "enhanced_search"
                response = self.rag_system.search_enhanced(query, top_k=8, use_summaries=True)
            else:
                search_method = "basic_search"
                response = self.rag_system.search_and_answer(query, top_k=8)
            
            # Log response
            answer_preview = response.answer[:150] + "..." if len(response.answer) > 150 else response.answer
            sources_count = len(response.sources)
            
            self.log_step(f"✅ Query SUCCESS", 
                         f"Method: {search_method}, Answer length: {len(response.answer)}, Sources: {sources_count}")
            print(f"    📝 Answer preview: {answer_preview}")
            print(f"    📚 Sources: {response.sources}")
            
            return response
            
        except Exception as e:
            self.log_step(f"❌ Query EXCEPTION", f"Error: {str(e)}")
            return None

    def step_5_clear_everything(self):
        """Step 5: Clear everything (🗑️ Clear All Documents & Chat button)"""
        self.log_step("STEP 5: Clear Everything Operation", "Simulating Clear All Documents & Chat button click")
        
        try:
            # Get status before clearing
            status_before = self.get_document_status()
            total_before = status_before.get('total_items', 0)
            
            self.log_step("📊 Before Clear", f"Total items: {total_before}")
            
            # Execute clear operation (simulates the clear_everything() function)
            # Step 1: Stop services
            self.log_step("🛑 Stopping Docker services...")
            result = subprocess.run(["docker-compose", "down"], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.log_step("❌ Docker stop FAILED", f"Error: {result.stderr}")
                return False
            
            time.sleep(3)
            
            # Step 2: Delete volume
            self.log_step("🗑️ Deleting persistent volume...")
            result = subprocess.run(
                ["docker", "volume", "rm", "rag-document-chat-ver2_chromadb_data"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                self.log_step("❌ Volume deletion FAILED", f"Error: {result.stderr}")
                return False
            
            # Step 3: Recreate ChromaDB
            self.log_step("🚀 Recreating ChromaDB...")
            result = subprocess.run(
                ["docker-compose", "up", "-d", "chromadb"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                self.log_step("❌ ChromaDB recreation FAILED", f"Error: {result.stderr}")
                return False
            
            # Step 4: Wait for readiness
            self.log_step("⏳ Waiting for ChromaDB to be ready...")
            import requests
            for i in range(15):
                try:
                    resp = requests.get("http://localhost:8002/api/v2/heartbeat", timeout=2)
                    if resp.status_code == 200:
                        self.log_step("✅ ChromaDB ready", f"Ready after {i*2} seconds")
                        break
                except:
                    time.sleep(2)
            else:
                self.log_step("❌ ChromaDB failed to become ready")
                return False
            
            time.sleep(5)  # Additional stabilization
            
            # Step 5: Reinitialize RAG system (simulates session state reset)
            self.log_step("🔄 Reinitializing RAG system...")
            self.rag_system = RAGSystem()
            
            # Step 6: Verify clean state
            status_after = self.get_document_status()
            total_after = status_after.get('total_items', 0)
            
            self.log_step("📊 After Clear", f"Total items: {total_after}")
            self.print_status("STATUS AFTER CLEAR OPERATION")
            
            if total_after == 0:
                self.log_step("✅ Clear Everything SUCCESS", f"Cleared {total_before} items successfully")
                return True
            else:
                self.log_step("❌ Clear Everything FAILED", f"{total_after} items remain after clear")
                return False
                
        except Exception as e:
            self.log_step("❌ Clear Everything EXCEPTION", f"Error: {str(e)}")
            return False

    def run_complete_workflow(self):
        """Run the complete Streamlit workflow test"""
        print("🚀 STARTING COMPLETE STREAMLIT WORKFLOW TEST")
        print("=" * 80)
        
        start_time = time.time()
        
        # Initial status
        self.rag_system = RAGSystem()
        self.print_status("INITIAL STATUS")
        
        # Test sequence
        steps = [
            ("Upload & Basic Chunks", self.step_1_upload_and_basic_chunks),
            ("Smart Summaries", self.step_2_smart_summaries),
            ("Paragraph Context", self.step_3_paragraph_context),
            ("Query Before Clear", lambda: self.step_4_query_documents("Query Before Clear") is not None),
            ("Clear Everything", self.step_5_clear_everything),
            ("Query After Clear", lambda: self.step_4_query_documents("Query After Clear") is not None),
        ]
        
        results = []
        
        for step_name, step_func in steps:
            print(f"\n🔄 EXECUTING: {step_name}")
            try:
                success = step_func()
                results.append((step_name, success))
                if success:
                    print(f"✅ {step_name}: SUCCESS")
                else:
                    print(f"❌ {step_name}: FAILED")
                    break
            except Exception as e:
                print(f"❌ {step_name}: EXCEPTION - {e}")
                results.append((step_name, False))
                break
            
            time.sleep(2)  # Brief pause between steps
        
        # Summary
        duration = time.time() - start_time
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        print(f"\n🏁 WORKFLOW TEST SUMMARY")
        print("=" * 80)
        print(f"📊 Results: {passed}/{total} steps passed")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        print()
        
        for step_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {step_name}")
        
        print("=" * 80)
        
        if passed == total:
            print("🎉 COMPLETE WORKFLOW SUCCESS: All steps passed!")
            return True
        else:
            print(f"💥 WORKFLOW FAILED: {total - passed} steps failed")
            return False

def main():
    test = StreamlitWorkflowTest()
    success = test.run_complete_workflow()
    
    # Cleanup
    try:
        import os
        if os.path.exists("comprehensive_test.txt"):
            os.remove("comprehensive_test.txt")
            print("🧹 Cleaned up test file")
    except:
        pass
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)