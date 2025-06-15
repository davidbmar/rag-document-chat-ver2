#!/usr/bin/env python3
"""
Full Integration Test for RAG Document Chat System
Tests the complete workflow: upload → process → query → clear → verify

This test simulates the actual Streamlit user workflow:
1. Upload test_simple.txt
2. Process Basic Chunks
3. Process Smart Summaries  
4. Process Paragraph Context
5. Query: "what documents have you indexed?"
6. Clear Everything
7. Query again: "what documents have you indexed?"
8. Verify system is clean
"""

import asyncio
import os
import sys
import time
import logging
import subprocess
import requests
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import the RAG system components
try:
    from rag_system import RAGSystem
    from models import ChatResponse
except ImportError as e:
    logger.error(f"Failed to import RAG components: {e}")
    sys.exit(1)

class IntegrationTest:
    def __init__(self):
        self.rag_system = None
        self.test_file_content = """This is a simple test document for the RAG system. It contains multiple paragraphs to test the document processing functionality. The system should be able to split this into logical chunks and create embeddings for search. This will help verify that the refactored system is working correctly with real OpenAI API integration."""
        self.test_filename = "test_simple.txt"
        self.results = {}
        self.start_time = datetime.now()
        
    def log_step(self, step: str, status: str, details: str = ""):
        """Log test step with consistent formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔄"
        logger.info(f"{status_emoji} [{timestamp}] {step}: {status}")
        if details:
            logger.info(f"    {details}")
        
        self.results[step] = {
            "status": status,
            "details": details,
            "timestamp": timestamp
        }

    def check_chromadb_status(self) -> bool:
        """Check if ChromaDB is running and accessible"""
        try:
            response = requests.get("http://localhost:8002/api/v2/heartbeat", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, int]:
        """Get current collection statistics"""
        stats = {}
        try:
            if not self.rag_system:
                return stats
            
            collections = self.rag_system.clients.chromadb.client.list_collections()
            for col in collections:
                try:
                    collection = self.rag_system.clients.chromadb.get_or_create_collection(col.name)
                    count = len(collection.get()['ids'])
                    stats[col.name] = count
                except Exception as e:
                    stats[col.name] = 0  # Default to 0 instead of error message
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            
        return stats

    def initialize_system(self) -> bool:
        """Initialize the RAG system"""
        try:
            self.log_step("System Initialization", "PROGRESS", "Initializing RAG system...")
            
            # Check ChromaDB first
            if not self.check_chromadb_status():
                self.log_step("System Initialization", "FAIL", "ChromaDB is not accessible")
                return False
            
            # Initialize RAG system
            self.rag_system = RAGSystem()
            
            # Verify system status
            status = self.rag_system.get_system_status()
            logger.info(f"System status: {status}")
            
            if status.get('chromadb') != 'connected':
                self.log_step("System Initialization", "FAIL", f"ChromaDB not connected: {status}")
                return False
                
            self.log_step("System Initialization", "PASS", f"RAG system initialized successfully")
            return True
            
        except Exception as e:
            self.log_step("System Initialization", "FAIL", f"Exception: {str(e)}")
            return False

    def create_test_file(self) -> bool:
        """Create the test file"""
        try:
            with open(self.test_filename, 'w') as f:
                f.write(self.test_file_content)
            
            self.log_step("Test File Creation", "PASS", f"Created {self.test_filename} ({len(self.test_file_content)} chars)")
            return True
            
        except Exception as e:
            self.log_step("Test File Creation", "FAIL", f"Exception: {str(e)}")
            return False

    def upload_and_process_basic_chunks(self) -> bool:
        """Step 1: Upload file and process basic chunks"""
        try:
            self.log_step("Basic Chunks Processing", "PROGRESS", "Processing document into basic chunks...")
            
            # Read file content
            with open(self.test_filename, 'rb') as f:
                content = f.read()
            
            # Process document (equivalent to clicking "Basic Chunks" button)
            result = asyncio.run(self.rag_system.process_document(content, self.test_filename))
            
            if result.status == "success":
                stats = self.get_collection_stats()
                self.log_step("Basic Chunks Processing", "PASS", 
                             f"Processing time: {result.processing_time:.2f}s, Collections: {stats}")
                return True
            else:
                self.log_step("Basic Chunks Processing", "FAIL", f"Result: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("Basic Chunks Processing", "FAIL", f"Exception: {str(e)}")
            return False

    def process_smart_summaries(self) -> bool:
        """Step 2: Process smart summaries"""
        try:
            self.log_step("Smart Summaries Processing", "PROGRESS", "Creating smart summaries...")
            
            # Process hierarchically (equivalent to clicking "Smart Summaries" button)
            result = asyncio.run(self.rag_system.process_document_hierarchically(self.test_filename))
            
            if result.status == "success":
                stats = self.get_collection_stats()
                compression_ratio = result.compression_stats.get('overall_compression_ratio', 0)
                self.log_step("Smart Summaries Processing", "PASS", 
                             f"Groups: {result.logical_groups_created}, Compression: {compression_ratio:.1f}:1, Collections: {stats}")
                return True
            else:
                self.log_step("Smart Summaries Processing", "FAIL", f"Result: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("Smart Summaries Processing", "FAIL", f"Exception: {str(e)}")
            return False

    def process_paragraph_context(self) -> bool:
        """Step 3: Process paragraph context"""
        try:
            self.log_step("Paragraph Context Processing", "PROGRESS", "Creating paragraph summaries...")
            
            # Process paragraphs (equivalent to clicking "Paragraph Context" button)
            result = asyncio.run(self.rag_system.process_document_paragraphs(self.test_filename))
            
            if result.status == "success":
                stats = self.get_collection_stats()
                compression_ratio = result.compression_stats.get('overall_compression_ratio', 0)
                self.log_step("Paragraph Context Processing", "PASS", 
                             f"Paragraphs: {result.paragraphs_processed}, Compression: {compression_ratio:.1f}:1, Collections: {stats}")
                return True
            else:
                self.log_step("Paragraph Context Processing", "FAIL", f"Result: {result.message}")
                return False
                
        except Exception as e:
            self.log_step("Paragraph Context Processing", "FAIL", f"Exception: {str(e)}")
            return False

    def query_indexed_documents(self, step_name: str) -> ChatResponse:
        """Query what documents have been indexed"""
        try:
            self.log_step(step_name, "PROGRESS", "Querying indexed documents...")
            
            query = "what documents have you indexed?"
            
            # Check what search path will be taken
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
            
            # Choose appropriate search method
            if has_paragraphs:
                search_method = "paragraph_search"
                response = self.rag_system.search_with_paragraphs(query, top_k_paragraphs=3, top_k_chunks=5)
            elif has_summaries:
                search_method = "enhanced_search"
                response = self.rag_system.search_enhanced(query, top_k=8, use_summaries=True)
            else:
                search_method = "basic_search"
                response = self.rag_system.search_and_answer(query, top_k=8)
            
            # Log the response details
            answer_preview = response.answer[:100] + "..." if len(response.answer) > 100 else response.answer
            sources_count = len(response.sources)
            
            self.log_step(step_name, "PASS", 
                         f"Method: {search_method}, Answer length: {len(response.answer)}, Sources: {sources_count}")
            logger.info(f"    Answer preview: {answer_preview}")
            logger.info(f"    Sources: {response.sources}")
            
            return response
            
        except Exception as e:
            self.log_step(step_name, "FAIL", f"Exception: {str(e)}")
            return None

    def clear_everything(self) -> bool:
        """Execute the clear everything operation"""
        try:
            self.log_step("Clear Everything Operation", "PROGRESS", "Starting comprehensive clear...")
            
            # Get stats before clearing
            stats_before = self.get_collection_stats()
            total_before = sum(v for v in stats_before.values() if isinstance(v, int))
            
            logger.info(f"    Before clear: {stats_before} (Total: {total_before} items)")
            
            # Execute clear operation using Docker approach
            # Step 1: Stop services
            logger.info("    Stopping Docker services...")
            result = subprocess.run(["docker-compose", "down"], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.log_step("Clear Everything Operation", "FAIL", f"docker-compose down failed: {result.stderr}")
                return False
            
            time.sleep(3)
            
            # Step 2: Delete volume
            logger.info("    Deleting persistent volume...")
            result = subprocess.run(
                ["docker", "volume", "rm", "rag-document-chat-ver2_chromadb_data"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                self.log_step("Clear Everything Operation", "FAIL", f"Volume deletion failed: {result.stderr}")
                return False
            
            # Step 3: Recreate ChromaDB
            logger.info("    Recreating ChromaDB...")
            result = subprocess.run(
                ["docker-compose", "up", "-d", "chromadb"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                self.log_step("Clear Everything Operation", "FAIL", f"ChromaDB recreation failed: {result.stderr}")
                return False
            
            # Step 4: Wait for readiness
            logger.info("    Waiting for ChromaDB to be ready...")
            for i in range(15):
                if self.check_chromadb_status():
                    logger.info(f"    ChromaDB ready after {i*2} seconds")
                    break
                time.sleep(2)
            else:
                self.log_step("Clear Everything Operation", "FAIL", "ChromaDB failed to become ready")
                return False
            
            time.sleep(5)  # Additional stabilization time
            
            # Step 5: Reinitialize RAG system
            logger.info("    Reinitializing RAG system...")
            self.rag_system = RAGSystem()
            
            # Step 6: Verify clean state
            stats_after = self.get_collection_stats()
            total_after = sum(v for v in stats_after.values() if isinstance(v, int))
            
            logger.info(f"    After clear: {stats_after} (Total: {total_after} items)")
            
            if total_after == 0:
                self.log_step("Clear Everything Operation", "PASS", 
                             f"Successfully cleared {total_before} items from {len(stats_before)} collections")
                return True
            else:
                self.log_step("Clear Everything Operation", "FAIL", 
                             f"Clear incomplete: {total_after} items remain in {len(stats_after)} collections")
                return False
                
        except Exception as e:
            self.log_step("Clear Everything Operation", "FAIL", f"Exception: {str(e)}")
            return False

    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            if os.path.exists(self.test_filename):
                os.remove(self.test_filename)
                logger.info(f"Cleaned up {self.test_filename}")
        except Exception as e:
            logger.error(f"Failed to cleanup test files: {e}")

    def print_summary(self):
        """Print test summary"""
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*80)
        print("🧪 FULL INTEGRATION TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        total = len([r for r in self.results.values() if r['status'] in ['PASS', 'FAIL']])
        
        print(f"📊 Results: {passed}/{total} tests passed ({failed} failed)")
        print(f"⏱️ Duration: {duration.total_seconds():.1f} seconds")
        print()
        
        for step, result in self.results.items():
            status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "🔄"
            print(f"{status_emoji} {step}: {result['status']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n" + "="*80)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED: Clear functionality is working correctly!")
            return True
        else:
            print(f"💥 {failed} TESTS FAILED: Clear functionality has issues!")
            return False

    def run_full_test(self) -> bool:
        """Run the complete integration test"""
        logger.info("🚀 Starting Full Integration Test")
        logger.info(f"Test started at: {self.start_time}")
        
        try:
            # Test sequence
            test_steps = [
                ("Initialize System", self.initialize_system),
                ("Create Test File", self.create_test_file),
                ("Process Basic Chunks", self.upload_and_process_basic_chunks),
                ("Process Smart Summaries", self.process_smart_summaries),
                ("Process Paragraph Context", self.process_paragraph_context),
                ("Query Before Clear", lambda: self.query_indexed_documents("Query Before Clear") is not None),
                ("Clear Everything", self.clear_everything),
                ("Query After Clear", lambda: self.query_indexed_documents("Query After Clear") is not None),
            ]
            
            # Execute test steps
            for step_name, step_func in test_steps:
                try:
                    success = step_func()
                    if not success:
                        logger.error(f"Test failed at step: {step_name}")
                        break
                except Exception as e:
                    self.log_step(step_name, "FAIL", f"Unexpected exception: {str(e)}")
                    break
                    
                # Brief pause between steps
                time.sleep(1)
            
            return self.print_summary()
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return False
        finally:
            self.cleanup_test_files()

def main():
    """Main test execution"""
    test = IntegrationTest()
    success = test.run_full_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()