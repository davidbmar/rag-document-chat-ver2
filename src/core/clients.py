#!/usr/bin/env python3
"""
Client managers for external services (OpenAI, ChromaDB, S3)
"""

import time
import logging
from typing import List, Optional, Dict, Any

import boto3
import chromadb
from openai import OpenAI

from src.core.config import config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI client with enhanced functionality"""
    
    def __init__(self):
        if not config.openai_enabled and not config.demo_mode:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        if config.demo_mode:
            self.client = None
            logger.info("🎭 Running in demo mode - OpenAI client disabled")
        else:
            self.client = OpenAI(api_key=config.openai_api_key)
            self._test_connection()
    
    def _test_connection(self):
        """Test OpenAI connection"""
        try:
            self.client.models.list()
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if config.demo_mode:
            # Return a dummy embedding for demo
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            # Create a simple hash-based "embedding"
            return [float(int(hash_obj.hexdigest()[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)][:1536]
        
        try:
            response = self.client.embeddings.create(
                model=config.embedding_model,
                input=text[:8191]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         temperature: float = 0.1, 
                         max_tokens: int = 1000) -> str:
        """Generate chat response"""
        if config.demo_mode:
            return "This is a demo response. In production mode, this would be generated by OpenAI's GPT model based on your documents."
        
        try:
            response = self.client.chat.completions.create(
                model=config.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat response generation failed: {e}")
            raise


class ChromaDBClient:
    """Wrapper for ChromaDB client with connection management"""
    
    def __init__(self):
        self.client = None
        self.collections = {}
        self._init_connection()
    
    def _init_connection(self):
        """Initialize ChromaDB connection with retries"""
        for attempt in range(3):
            try:
                logger.info(f"🔄 Connecting to ChromaDB (attempt {attempt + 1}/3)...")
                
                self.client = chromadb.HttpClient(
                    host=config.chroma_host,
                    port=config.chroma_port
                )
                
                self.client.heartbeat()
                logger.info("✅ ChromaDB server connected")
                return
                
            except Exception as e:
                logger.warning(f"❌ ChromaDB connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)
        
        logger.info("⚠️ Using in-memory ChromaDB (data will not persist)")
        self.client = chromadb.Client()
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> Any:
        """Get or create a collection"""
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {}
            )
        return self.collections[name]
    
    def heartbeat(self) -> bool:
        """Check if connection is alive"""
        try:
            if hasattr(self.client, 'heartbeat'):
                self.client.heartbeat()
                return True
            return True  # In-memory client
        except:
            return False


class S3Client:
    """Wrapper for S3 client with enhanced functionality"""
    
    def __init__(self):
        self.client = None
        if config.s3_enabled:
            self._init_connection()
    
    def _init_connection(self):
        """Initialize S3 connection"""
        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.aws_region
            )
            logger.info("✅ S3 client initialized")
        except Exception as e:
            logger.warning(f"⚠️ S3 initialization failed: {e}")
            self.client = None
    
    def upload_file(self, file_content: bytes, filename: str, metadata: Optional[Dict] = None) -> bool:
        """Upload file to S3"""
        if not self.client:
            return False
        
        try:
            self.client.put_object(
                Bucket=config.s3_bucket,
                Key=f"documents/{filename}",
                Body=file_content,
                Metadata=metadata or {'original_name': filename}
            )
            logger.info(f"☁️ Uploaded to S3: {filename}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ S3 upload failed: {e}")
            return False
    
    def check_bucket_access(self) -> bool:
        """Check if bucket is accessible"""
        if not self.client:
            return False
        
        try:
            self.client.head_bucket(Bucket=config.s3_bucket)
            return True
        except:
            return False


class ClientManager:
    """Central manager for all external clients"""
    
    def __init__(self):
        self.openai = OpenAIClient()
        self.chromadb = ChromaDBClient()
        self.s3 = S3Client()
    
    def get_status(self) -> Dict[str, str]:
        """Get status of all clients"""
        status = {
            "openai": "connected" if self.openai else "disconnected",
            "chromadb": "connected" if self.chromadb.heartbeat() else "disconnected",
            "s3": "disabled"
        }
        
        if config.s3_enabled and self.s3.client:
            status["s3"] = "connected" if self.s3.check_bucket_access() else "error"
        
        return status