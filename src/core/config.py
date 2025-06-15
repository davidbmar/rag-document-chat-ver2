#!/usr/bin/env python3
"""
Configuration management for RAG Document Chat System
"""

import os
from dataclasses import dataclass
from typing import Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass


@dataclass
class Config:
    """System configuration from environment variables"""
    
    # API Keys
    openai_api_key: str = ""
    
    # AWS Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    
    # ChromaDB Configuration
    chroma_host: str = "localhost"
    chroma_port: int = 8002
    
    # API Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    
    # Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100
    max_chunks: int = 15
    
    # Model Configuration
    embedding_model: str = "text-embedding-ada-002"
    chat_model: str = "gpt-3.5-turbo"
    
    # PDF Processing Configuration
    pdf_library: str = "pymupdf"  # "pymupdf" or "pypdf2"
    
    # Demo mode
    demo_mode: bool = False
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_BUCKET", "")
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8002"))
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8003"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
        self.max_chunks = int(os.getenv("MAX_CHUNKS", "15"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.chat_model = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
        self.pdf_library = os.getenv("PDF_LIBRARY", "pymupdf").lower()
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    @property
    def s3_enabled(self) -> bool:
        """Check if S3 is properly configured"""
        return bool(self.s3_bucket and self.aws_access_key_id and self.aws_secret_access_key)
    
    @property
    def openai_enabled(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))
    
    @property
    def api_url(self) -> str:
        """Get the full API URL"""
        return f"http://{self.api_host}:{self.api_port}"
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return status and errors"""
        errors = []
        
        if not self.demo_mode and not self.openai_enabled:
            errors.append("OpenAI API key is required and must start with 'sk-' (or set DEMO_MODE=true)")
        
        if self.chunk_size <= 0:
            errors.append("Chunk size must be positive")
        
        if self.chunk_overlap < 0:
            errors.append("Chunk overlap cannot be negative")
        
        if self.chunk_overlap >= self.chunk_size:
            errors.append("Chunk overlap must be less than chunk size")
        
        if self.chroma_port <= 0 or self.chroma_port > 65535:
            errors.append("ChromaDB port must be between 1 and 65535")
        
        if self.pdf_library not in ["pymupdf", "pypdf2"]:
            errors.append("PDF_LIBRARY must be either 'pymupdf' or 'pypdf2'")
        
        return len(errors) == 0, errors


# Global configuration instance
config = Config()