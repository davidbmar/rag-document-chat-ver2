#!/usr/bin/env python3
"""
Utility functions for RAG Document Chat System
"""

import os
import sys
import hashlib
import logging
from typing import Dict, Any

try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    nltk = None


def setup_logging() -> logging.Logger:
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def ensure_nltk_data():
    """Download required NLTK data if not present"""
    if not NLTK_AVAILABLE:
        return
        
    required_data = [
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('tokenizers/punkt', 'punkt'),
        ('corpora/stopwords', 'stopwords')
    ]
    
    for path, name in required_data:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"Downloading NLTK {name} data...")
            nltk.download(name)


def calculate_hash(text: str) -> str:
    """Calculate MD5 hash for text"""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def get_system_status(chroma_client, openai_client, s3_client, config) -> Dict[str, str]:
    """Get system component status"""
    status = {
        "chromadb": "disconnected",
        "openai": "disconnected", 
        "s3": "disabled"
    }
    
    # Check ChromaDB
    try:
        if hasattr(chroma_client, 'heartbeat'):
            chroma_client.heartbeat()
            status["chromadb"] = "connected"
        else:
            status["chromadb"] = "in-memory"
    except:
        status["chromadb"] = "disconnected"
    
    # Check OpenAI
    if config.openai_enabled:
        try:
            openai_client.models.list()
            status["openai"] = "connected"
        except:
            status["openai"] = "error"
    
    # Check S3
    if config.s3_enabled and s3_client:
        try:
            s3_client.head_bucket(Bucket=config.s3_bucket)
            status["s3"] = "connected"
        except:
            status["s3"] = "error"
    
    return status


def print_usage():
    """Print usage information"""
    print("Usage: python app.py [streamlit|api]")
    print("  streamlit - Run web interface (default)")
    print("  api      - Run API server")
    sys.exit(1)