#!/usr/bin/env python3
"""Test script to verify RAG system setup"""

import os
import sys
from typing import Dict

def test_imports() -> bool:
    """Test that all required packages can be imported"""
    try:
        import chromadb
        import openai
        import streamlit
        import fastapi
        import boto3
        import PyPDF2
        import langchain
        import nltk  # New addition
        print("✅ All Python packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_chromadb() -> bool:
    """Test ChromaDB connection"""
    try:
        import chromadb
        client = chromadb.HttpClient(host="localhost", port=8002)
        client.heartbeat()
        print("✅ ChromaDB connection successful")
        return True
    except Exception as e:
        print(f"⚠️ ChromaDB connection failed: {e}")
        print("   Trying in-memory mode...")
        try:
            client = chromadb.Client()
            collection = client.get_or_create_collection("test")
            print("✅ ChromaDB in-memory mode working")
            return True
        except Exception as e2:
            print(f"❌ ChromaDB completely failed: {e2}")
            return False

def test_nltk() -> bool:
    """Test NLTK functionality"""
    try:
        import nltk
        # Test sentence tokenization
        test_text = "Hello world. This is Dr. Smith. He went to the store."
        tokens = nltk.sent_tokenize(test_text)
        if len(tokens) >= 2:
            print("✅ NLTK sentence tokenization working")
            return True
        else:
            print("⚠️ NLTK tokenization returned unexpected results")
            return False
    except Exception as e:
        print(f"❌ NLTK test failed: {e}")
        return False

def test_openai() -> bool:
    """Test OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY not set in environment")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️ OPENAI_API_KEY doesn't look valid (should start with 'sk-')")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.models.list()
        print("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_s3() -> bool:
    """Test S3 configuration (optional)"""
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        print("ℹ️ S3 not configured (optional)")
        return True
    
    try:
        import boto3
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket)
        print("✅ S3 connection successful")
        return True
    except Exception as e:
        print(f"⚠️ S3 test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing RAG System Setup")
    print("=" * 30)
    
    tests = [
        ("Package Imports", test_imports),
        ("ChromaDB", test_chromadb),
        ("NLTK", test_nltk),
        ("OpenAI API", test_openai),
        ("S3 (Optional)", test_s3)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing {name}...")
        results.append(test_func())
    
    print("\n" + "=" * 30)
    print("📊 Test Results:")
    for i, (name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {name}: {status}")
    
    required_tests = results[:3]  # Imports, ChromaDB, and NLTK
    if all(required_tests):
        print("\n🎉 Core system is ready!")
        print("   Run: streamlit run app.py")
    else:
        print("\n❌ Setup incomplete. Please check the failed tests above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
