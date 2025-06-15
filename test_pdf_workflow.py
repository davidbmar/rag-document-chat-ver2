#!/usr/bin/env python3
"""
Test script to verify PDF processing workflow with PyMuPDF
"""

import sys
import os
import asyncio
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.search.rag_system import RAGSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_pdf_workflow():
    """Test the complete PDF processing workflow"""
    
    print("=== RAG System PDF Processing Test ===")
    
    # Test PDF file
    test_pdf_path = "test_documents/CapsuleHandbookVersion2024.Jan1.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found at {test_pdf_path}")
        return False
    
    try:
        # Initialize RAG system
        print("🔧 Initializing RAG system...")
        rag_system = RAGSystem()
        
        # Test document processing
        print(f"📄 Processing PDF: {test_pdf_path}")
        
        with open(test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Process the document
        result = await rag_system.process_document(pdf_content, "test_handbook.pdf")
        
        print(f"📊 Processing result:")
        print(f"   Status: {result.status}")
        print(f"   Message: {result.message}")
        print(f"   Chunks created: {result.chunks_created}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        
        if result.status == "success":
            print("✅ Document processing successful!")
            
            # Test search functionality
            print("\n🔍 Testing search functionality...")
            search_result = rag_system.search_and_answer("team member handbook", top_k=3)
            
            print(f"📋 Search and answer result:")
            print(f"   Status: {search_result.status}")
            print(f"   Answer preview: {search_result.answer[:200]}...")
            
            if search_result.sources:
                print(f"   Sources found: {len(search_result.sources)}")
                
                for i, source in enumerate(search_result.sources[:2]):
                    print(f"\n   Source {i+1}:")
                    print(f"     Content preview: {source[:100]}...")
                    
                    # Check for spacing issues in the content
                    if "m em ber" in source or "tim e" in source:
                        print("⚠️  WARNING: Spacing issues detected in search results")
                        return False
                    else:
                        print("✅ No spacing issues detected in this source")
            
            print("\n✅ Complete workflow test successful!")
            return True
        else:
            print(f"❌ Document processing failed: {result.message}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        logger.exception("Full error details:")
        return False

if __name__ == "__main__":
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    print()
    
    success = asyncio.run(test_pdf_workflow())
    
    if success:
        print("\n🎉 All tests passed! PyMuPDF is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed! Check the logs above.")
        sys.exit(1)