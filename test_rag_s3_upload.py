#!/usr/bin/env python3
"""
Test script to verify S3 upload functionality in RAG system
"""

import os
import sys
import logging
from io import BytesIO

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add current directory to path to import app
sys.path.insert(0, '.')

try:
    from app import rag_system, config
    print("✅ Successfully imported RAG system")
except ImportError as e:
    print(f"❌ Failed to import RAG system: {e}")
    print("Make sure you're in the RAG project directory and virtual environment is activated")
    sys.exit(1)

def test_s3_configuration():
    """Test S3 configuration and connection"""
    print("\n🔧 Testing S3 Configuration")
    print("=" * 30)
    
    print(f"S3 Enabled: {config.s3_enabled}")
    print(f"S3 Bucket: {config.S3_BUCKET}")
    print(f"AWS Region: {config.AWS_REGION}")
    print(f"S3 Client Initialized: {rag_system.s3_client is not None}")
    
    if rag_system.s3_client:
        try:
            # Test S3 connection
            rag_system.s3_client.head_bucket(Bucket=config.S3_BUCKET)
            print("✅ S3 connection successful")
            return True
        except Exception as e:
            print(f"❌ S3 connection failed: {e}")
            return False
    else:
        print("❌ S3 client not initialized")
        return False

def create_test_document():
    """Create a simple test document"""
    test_content = """
# Test Document for RAG System

This is a test document to verify that the RAG system can:
1. Process documents
2. Upload them to S3
3. Create embeddings
4. Store in ChromaDB

## Key Information

The RAG system uses OpenAI embeddings and stores documents in ChromaDB.
When S3 is configured, original documents are also backed up to S3.

## Test Query Answers

Question: What does this test document verify?
Answer: This document verifies that the RAG system can process documents, upload to S3, create embeddings, and store in ChromaDB.
"""
    return test_content.encode('utf-8')

async def test_document_processing():
    """Test the complete document processing pipeline"""
    print("\n📄 Testing Document Processing")
    print("=" * 30)
    
    # Create test document
    test_filename = "test_document.txt"
    test_content = create_test_document()
    
    print(f"📝 Processing test document: {test_filename}")
    print(f"📊 Document size: {len(test_content)} bytes")
    
    try:
        # Process the document (this should trigger S3 upload if configured)
        result = await rag_system.process_document(test_content, test_filename)
        
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        print(f"Chunks Created: {result.chunks_created}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        
        if result.status == "success":
            print("✅ Document processing successful")
            
            # Check if file exists in S3
            if rag_system.s3_client:
                try:
                    rag_system.s3_client.head_object(
                        Bucket=config.S3_BUCKET,
                        Key=f"documents/{test_filename}"
                    )
                    print("✅ File found in S3!")
                    
                    # Clean up test file
                    rag_system.s3_client.delete_object(
                        Bucket=config.S3_BUCKET,
                        Key=f"documents/{test_filename}"
                    )
                    print("🧹 Cleaned up test file from S3")
                    
                except Exception as e:
                    print(f"❌ File not found in S3: {e}")
            
            return True
        else:
            print(f"❌ Document processing failed: {result.message}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during processing: {e}")
        return False

def test_search_functionality():
    """Test search and answer functionality"""
    print("\n🔍 Testing Search Functionality")
    print("=" * 30)
    
    try:
        result = rag_system.search_and_answer("What does this test document verify?")
        print(f"Answer: {result.answer}")
        print(f"Sources: {result.sources}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print("✅ Search functionality working")
        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 RAG System S3 Upload Test")
    print("=" * 40)
    
    # Test S3 configuration
    s3_ok = test_s3_configuration()
    
    # Test document processing (includes S3 upload)
    processing_ok = await test_document_processing()
    
    # Test search functionality
    search_ok = test_search_functionality()
    
    print("\n📊 Test Results Summary")
    print("=" * 25)
    print(f"S3 Configuration: {'✅ PASS' if s3_ok else '❌ FAIL'}")
    print(f"Document Processing: {'✅ PASS' if processing_ok else '❌ FAIL'}")
    print(f"Search Functionality: {'✅ PASS' if search_ok else '❌ FAIL'}")
    
    if all([s3_ok, processing_ok, search_ok]):
        print("\n🎉 All tests passed! S3 upload is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    import asyncio
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
