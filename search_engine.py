#!/usr/bin/env python3
"""
Search and retrieval engine for RAG Document Chat System
"""

import time
import logging
from typing import List, Dict, Any

from models import ChatResponse
from clients import ClientManager

logger = logging.getLogger(__name__)


class SearchEngine:
    """Enhanced search engine with multiple retrieval strategies"""
    
    def __init__(self, client_manager: ClientManager):
        self.clients = client_manager
        
        # Get collections
        self.document_collection = self.clients.chromadb.get_or_create_collection(
            "documents",
            {"description": "RAG document collection"}
        )
        
        self.summary_collection = self.clients.chromadb.get_or_create_collection(
            "logical_summaries",
            {"description": "10:1 compressed summaries of logical groups"}
        )
        
        self.paragraph_collection = self.clients.chromadb.get_or_create_collection(
            "paragraph_summaries",
            {"description": "Paragraph-level summaries for wider context search"}
        )
    
    def search_and_answer(self, query: str, top_k: int = 3) -> ChatResponse:
        """Search documents and generate answer using RAG"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing query: {query}")
            
            # Generate query embedding
            query_embedding = self.clients.openai.get_embedding(query)
            
            # Search for relevant chunks
            results = self.document_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if not results['documents'][0]:
                return ChatResponse(
                    answer="No relevant documents found. Please upload some documents first.",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            # Prepare context
            context_chunks = results['documents'][0]
            context = "\n\n".join(context_chunks)
            sources = [meta["filename"] for meta in results['metadatas'][0]]
            
            logger.info(f"📚 Found {len(context_chunks)} relevant chunks from {len(set(sources))} documents")
            
            # Generate answer
            answer = self._generate_answer(query, context)
            processing_time = time.time() - start_time
            
            logger.info(f"💬 Generated answer in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=list(set(sources)),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Search and answer failed: {e}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def search_enhanced(self, query: str, top_k: int = 5, use_summaries: bool = True) -> ChatResponse:
        """Enhanced search that uses both chunks and summaries"""
        start_time = time.time()
        
        try:
            if not use_summaries:
                return self.search_and_answer(query, top_k)
            
            # Get regular chunk search results
            chunk_response = self.search_and_answer(query, top_k)
            
            # Search summaries
            query_embedding = self.clients.openai.get_embedding(query)
            summary_results = self.summary_collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            
            if not summary_results['documents'][0]:
                return chunk_response
            
            # Combine contexts
            chunk_context = "\n\n".join(chunk_response.sources)
            summary_context = "\n\n".join([
                f"Summary: {doc}" for doc in summary_results['documents'][0]
            ])
            
            combined_context = f"Detailed Chunks:\n{chunk_context}\n\nLogical Summaries:\n{summary_context}"
            
            # Generate enhanced answer
            enhanced_answer = self._generate_enhanced_answer(query, combined_context)
            
            # Combine sources
            summary_sources = [f"Summary: {meta['filename']}" for meta in summary_results['metadatas'][0]]
            combined_sources = chunk_response.sources + summary_sources
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                answer=enhanced_answer,
                sources=combined_sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.warning(f"Enhanced search failed, falling back to basic search: {e}")
            return self.search_and_answer(query, top_k)
    
    def search_with_location_info(self, query: str, top_k: int = 3) -> ChatResponse:
        """Search with enhanced location information"""
        start_time = time.time()
        
        try:
            query_embedding = self.clients.openai.get_embedding(query)
            
            results = self.document_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if not results['documents'][0]:
                return ChatResponse(
                    answer="No relevant documents found. Please upload some documents first.",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            # Prepare enhanced context with location information
            context_chunks = []
            source_info = []
            
            for i, (chunk, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                location_ref = metadata.get('location_reference', 'Unknown location')
                summary = metadata.get('chunk_summary', 'No summary available')
                
                enhanced_chunk = f"[Source: {location_ref}]\n{chunk}\n[Summary: {summary}]\n"
                context_chunks.append(enhanced_chunk)
                
                source_detail = f"{metadata['filename']} ({location_ref})"
                source_info.append(source_detail)
            
            context = "\n---\n".join(context_chunks)
            
            # Generate answer with location awareness
            answer = self._generate_location_aware_answer(query, context)
            processing_time = time.time() - start_time
            
            return ChatResponse(
                answer=answer,
                sources=source_info,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Location-aware search failed: {e}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def _generate_answer(self, query: str, context: str) -> str:
        """Generate basic answer from context"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on provided context. "
                          "If the context doesn't contain enough information to answer the question, "
                          "say so clearly. Always be accurate and cite the information from the context."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def _generate_enhanced_answer(self, query: str, combined_context: str) -> str:
        """Generate enhanced answer using both chunks and summaries"""
        messages = [
            {
                "role": "system",
                "content": "Use both detailed chunks and logical summaries to provide comprehensive answers. "
                          "Summaries give broader context, chunks provide specific details."
            },
            {
                "role": "user",
                "content": f"Context:\n{combined_context}\n\nQuestion: {query}\n\nAnswer:"
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def _generate_location_aware_answer(self, query: str, context: str) -> str:
        """Generate answer with location information"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on provided context. "
                          "Each source includes location information in brackets. "
                          "When referencing information, mention the specific location (page, section) when available. "
                          "If the context doesn't contain enough information to answer the question, "
                          "say so clearly. Always be accurate and cite the information from the context."
            },
            {
                "role": "user",
                "content": f"Context with location information:\n{context}\n\nQuestion: {query}\n\n"
                          "Answer the question and reference specific locations when mentioning information:"
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def search_with_paragraphs(self, query: str, top_k_paragraphs: int = 3, top_k_chunks: int = 5) -> ChatResponse:
        """Search using paragraph summaries for wider context plus detailed chunks"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing query with paragraph context: {query}")
            
            # Get detailed chunk search
            chunk_response = self.search_and_answer(query, top_k_chunks)
            
            # Search paragraph summaries
            query_embedding = self.clients.openai.get_embedding(query)
            paragraph_results = self.paragraph_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k_paragraphs
            )
            
            if not paragraph_results['documents'][0]:
                return chunk_response
            
            # Combine contexts with paragraph summaries providing wider context
            chunk_context = "\n\n".join(chunk_response.sources) if chunk_response.sources else ""
            
            paragraph_context = "\n\n".join([
                f"Paragraph Context: {doc}" for doc in paragraph_results['documents'][0]
            ])
            
            combined_context = f"Detailed Information:\n{chunk_context}\n\nWider Context (Paragraph Summaries):\n{paragraph_context}"
            
            # Generate enhanced answer with paragraph context
            enhanced_answer = self._generate_paragraph_aware_answer(query, combined_context)
            
            # Combine sources
            paragraph_sources = [f"Paragraph: {meta['filename']}" for meta in paragraph_results['metadatas'][0]]
            combined_sources = chunk_response.sources + paragraph_sources
            
            processing_time = time.time() - start_time
            
            logger.info(f"📚 Found {len(paragraph_results['documents'][0])} paragraph contexts and {len(chunk_response.sources)} detail chunks")
            
            return ChatResponse(
                answer=enhanced_answer,
                sources=combined_sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.warning(f"Paragraph search failed, falling back to basic search: {e}")
            return self.search_and_answer(query, top_k_chunks)
    
    def _generate_paragraph_aware_answer(self, query: str, combined_context: str) -> str:
        """Generate answer using both paragraph context and detailed chunks"""
        messages = [
            {
                "role": "system",
                "content": "Use both detailed information and wider paragraph context to provide comprehensive answers. "
                          "Paragraph summaries give broader context and themes, detailed information provides specific facts."
            },
            {
                "role": "user",
                "content": f"Context:\n{combined_context}\n\nQuestion: {query}\n\n"
                          "Answer using both the detailed information and broader paragraph context:"
            }
        ]
        
        return self.clients.openai.generate_response(messages)