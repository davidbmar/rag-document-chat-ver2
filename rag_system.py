#!/usr/bin/env python3
"""
Main RAG System orchestrating all components
"""

import logging
from typing import Dict

from config import config
from clients import ClientManager
from document_processor import DocumentProcessor
from search_engine import SearchEngine
from hierarchical_processor import HierarchicalProcessor
from paragraph_processor import ParagraphProcessor
from models import DocumentResponse, ChatResponse
from utils import setup_logging, ensure_nltk_data

logger = setup_logging()


class RAGSystem:
    """Main RAG system implementation coordinating all components"""
    
    def __init__(self):
        logger.info("Initializing RAG System...")
        
        # Ensure NLTK data is available
        ensure_nltk_data()
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize client manager
        self.clients = ClientManager()
        
        # Initialize processing components
        self.document_processor = DocumentProcessor(self.clients)
        self.search_engine = SearchEngine(self.clients)
        self.hierarchical_processor = HierarchicalProcessor(self.clients)
        self.paragraph_processor = ParagraphProcessor(self.clients)
        
        logger.info("✅ RAG System initialized successfully")
    
    async def process_document(self, file_content: bytes, filename: str) -> DocumentResponse:
        """Process uploaded document"""
        return await self.document_processor.process_document(file_content, filename)
    
    def search_and_answer(self, query: str, top_k: int = 3, conversation_history: str = "") -> ChatResponse:
        """Basic search and answer with optional conversation history"""
        return self.search_engine.search_and_answer(query, top_k, conversation_history)
    
    def search_enhanced(self, query: str, top_k: int = 5, use_summaries: bool = True, conversation_history: str = "") -> ChatResponse:
        """Enhanced search with summaries and optional conversation history"""
        return self.search_engine.search_enhanced(query, top_k, use_summaries, conversation_history)
    
    def search_with_location_info(self, query: str, top_k: int = 3, conversation_history: str = "") -> ChatResponse:
        """Search with location information and optional conversation history"""
        return self.search_engine.search_with_location_info(query, top_k, conversation_history)
    
    def search_with_paragraphs(self, query: str, top_k_paragraphs: int = 3, top_k_chunks: int = 5, conversation_history: str = "") -> ChatResponse:
        """Search with paragraph context for wider understanding and optional conversation history"""
        return self.search_engine.search_with_paragraphs(query, top_k_paragraphs, top_k_chunks, conversation_history)
    
    async def process_document_hierarchically(self, filename: str):
        """Process document with hierarchical compression"""
        return await self.hierarchical_processor.process_document_hierarchically(filename)
    
    async def process_document_paragraphs(self, filename: str):
        """Process document with paragraph-level summaries"""
        return await self.paragraph_processor.process_document_paragraphs(filename)
    
    def get_system_status(self) -> Dict[str, str]:
        """Get system status"""
        return self.clients.get_status()