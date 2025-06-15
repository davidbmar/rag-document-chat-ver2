#!/usr/bin/env python3
"""
Search and retrieval engine for RAG Document Chat System
"""

import time
import uuid
import logging
from typing import List, Dict, Any, Optional

from models import ChatResponse, SearchRequest, SearchResponse, SearchResult, AskRequest
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
        
        # Store for search result persistence
        self._search_cache = {}
    
    def search_documents(self, request: SearchRequest) -> SearchResponse:
        """Enhanced search with filtering and result persistence"""
        start_time = time.time()
        search_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🔍 Enhanced search query: {request.query}")
            
            # Generate query embedding
            query_embedding = self.clients.openai.get_embedding(request.query)
            
            # Determine which collections to search
            collections_to_search = []
            if request.collections:
                if "documents" in request.collections:
                    collections_to_search.append(("documents", self.document_collection))
                if "summaries" in request.collections:
                    collections_to_search.append(("logical_summaries", self.summary_collection))
                if "paragraphs" in request.collections:
                    collections_to_search.append(("paragraph_summaries", self.paragraph_collection))
            else:
                # Search all collections by default
                collections_to_search = [
                    ("documents", self.document_collection),
                    ("logical_summaries", self.summary_collection),
                    ("paragraph_summaries", self.paragraph_collection)
                ]
            
            all_results = []
            collections_searched = []
            
            for collection_name, collection in collections_to_search:
                try:
                    # Build where clause for filtering
                    where_clause = {}
                    if request.documents:
                        where_clause["filename"] = {"$in": request.documents}
                    elif request.exclude_documents:
                        where_clause["filename"] = {"$nin": request.exclude_documents}
                    
                    # Search this collection
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=request.top_k,
                        where=where_clause if where_clause else None
                    )
                    
                    collections_searched.append(collection_name)
                    
                    # Process results
                    if results['documents'][0]:
                        for i, (content, metadata, distance) in enumerate(zip(
                            results['documents'][0],
                            results['metadatas'][0],
                            results['distances'][0]
                        )):
                            # Convert distance to similarity score
                            score = 1 - distance if distance < 1 else 0
                            
                            # Apply threshold filter
                            if request.threshold and score < request.threshold:
                                continue
                            
                            chunk_id = results['ids'][0][i]
                            
                            result = SearchResult(
                                content=content,
                                score=round(score, 4),
                                document=metadata.get('filename', 'unknown'),
                                chunk_id=chunk_id,
                                collection=collection_name,
                                metadata=metadata
                            )
                            all_results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort all results by score
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            # Limit to requested number
            all_results = all_results[:request.top_k]
            
            # Extract unique documents and chunk IDs
            unique_documents = list(set(result.document for result in all_results))
            chunk_ids = [result.chunk_id for result in all_results]
            
            response = SearchResponse(
                results=all_results,
                search_id=search_id,
                query=request.query,
                total_results=len(all_results),
                unique_documents=unique_documents,
                chunk_ids=chunk_ids,
                processing_time=time.time() - start_time,
                collections_searched=collections_searched
            )
            
            # Cache search results for reuse
            self._search_cache[search_id] = response
            
            logger.info(f"📚 Found {len(all_results)} results across {len(collections_searched)} collections")
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            return SearchResponse(
                results=[],
                search_id=search_id,
                query=request.query,
                total_results=0,
                unique_documents=[],
                chunk_ids=[],
                processing_time=time.time() - start_time,
                collections_searched=[]
            )
    
    def ask_with_context(self, request: AskRequest) -> ChatResponse:
        """Ask questions using filtered search results or cached search"""
        start_time = time.time()
        
        try:
            logger.info(f"💬 Processing question: {request.question}")
            
            # Determine context source
            context_chunks = []
            sources = []
            
            if request.search_id and request.search_id in self._search_cache:
                # Use cached search results
                cached_search = self._search_cache[request.search_id]
                context_chunks = [result.content for result in cached_search.results[:request.top_k]]
                sources = [f"{result.document} (via search)" for result in cached_search.results[:request.top_k]]
                logger.info(f"📋 Using cached search results: {len(context_chunks)} chunks")
                
            elif request.chunk_ids:
                # Use specific chunks
                context_chunks, sources = self._get_chunks_by_ids(request.chunk_ids)
                logger.info(f"🎯 Using specific chunks: {len(context_chunks)} chunks")
                
            else:
                # Perform new search with filtering
                search_request = SearchRequest(
                    query=request.question,
                    top_k=request.top_k,
                    documents=request.documents,
                    exclude_documents=request.exclude_documents
                )
                search_response = self.search_documents(search_request)
                
                context_chunks = [result.content for result in search_response.results]
                sources = [result.document for result in search_response.results]
                logger.info(f"🔍 New search found: {len(context_chunks)} chunks")
            
            if not context_chunks:
                return ChatResponse(
                    answer="No relevant content found for your question. Please check your search criteria or upload relevant documents.",
                    sources=[],
                    processing_time=time.time() - start_time
                )
            
            # Generate answer using appropriate strategy
            context = "\n\n".join(context_chunks)
            
            if request.search_strategy == "paragraph":
                answer = self._generate_paragraph_answer(request.question, context, request.conversation_history)
            elif request.search_strategy == "enhanced":
                answer = self._generate_enhanced_answer(request.question, context, request.conversation_history)
            else:
                answer = self._generate_answer(request.question, context, request.conversation_history)
            
            processing_time = time.time() - start_time
            
            logger.info(f"💬 Generated answer in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=list(set(sources)),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Ask with context failed: {e}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def _get_chunks_by_ids(self, chunk_ids: List[str]) -> tuple[List[str], List[str]]:
        """Retrieve specific chunks by their IDs"""
        context_chunks = []
        sources = []
        
        # Search across all collections for the chunk IDs
        collections = [
            ("documents", self.document_collection),
            ("logical_summaries", self.summary_collection),
            ("paragraph_summaries", self.paragraph_collection)
        ]
        
        for collection_name, collection in collections:
            try:
                # Get chunks by ID
                results = collection.get(ids=chunk_ids)
                
                if results['documents']:
                    for i, content in enumerate(results['documents']):
                        if i < len(results['metadatas']) and results['metadatas'][i]:
                            filename = results['metadatas'][i].get('filename', 'unknown')
                            context_chunks.append(content)
                            sources.append(f"{filename} ({collection_name})")
                            
            except Exception as e:
                logger.warning(f"Error getting chunks from {collection_name}: {e}")
                continue
        
        return context_chunks, sources
    
    def search_and_answer(self, query: str, top_k: int = 3, conversation_history: str = "") -> ChatResponse:
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
            
            # Generate answer with conversation history
            answer = self._generate_answer(query, context, conversation_history)
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
    
    def search_enhanced(self, query: str, top_k: int = 5, use_summaries: bool = True, conversation_history: str = "") -> ChatResponse:
        """Enhanced search that uses both chunks and summaries"""
        start_time = time.time()
        
        try:
            if not use_summaries:
                return self.search_and_answer(query, top_k, conversation_history)
            
            # Get regular chunk search results
            chunk_response = self.search_and_answer(query, top_k, conversation_history)
            
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
            enhanced_answer = self._generate_enhanced_answer(query, combined_context, conversation_history)
            
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
            return self.search_and_answer(query, top_k, conversation_history)
    
    def search_with_location_info(self, query: str, top_k: int = 3, conversation_history: str = "") -> ChatResponse:
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
            answer = self._generate_location_aware_answer(query, context, conversation_history)
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
    
    def _generate_answer(self, query: str, context: str, conversation_history: str = "") -> str:
        """Generate basic answer from context with optional conversation history"""
        
        # Build system message
        system_content = ("You are a helpful assistant that answers questions based on provided context. "
                         "If the context doesn't contain enough information to answer the question, "
                         "say so clearly. Always be accurate and cite the information from the context.")
        
        if conversation_history:
            system_content += (" You also have access to recent conversation history to understand "
                             "context and references like 'it', 'that', 'the previous topic', etc.")
        
        # Build user message
        user_content = f"Context:\n{context}"
        
        if conversation_history:
            user_content += f"\n\nRecent Conversation:\n{conversation_history}"
        
        user_content += f"\n\nQuestion: {query}\n\nAnswer:"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def _generate_enhanced_answer(self, query: str, combined_context: str, conversation_history: str = "") -> str:
        """Generate enhanced answer using both chunks and summaries with optional conversation history"""
        
        # Build system message
        system_content = ("Use both detailed chunks and logical summaries to provide comprehensive answers. "
                         "Summaries give broader context, chunks provide specific details.")
        
        if conversation_history:
            system_content += (" You also have access to recent conversation history to understand "
                             "context and references like 'it', 'that', 'the previous topic', etc.")
        
        # Build user message
        user_content = f"Context:\n{combined_context}"
        
        if conversation_history:
            user_content += f"\n\nRecent Conversation:\n{conversation_history}"
        
        user_content += f"\n\nQuestion: {query}\n\nAnswer:"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def _generate_location_aware_answer(self, query: str, context: str, conversation_history: str = "") -> str:
        """Generate answer with location information and optional conversation history"""
        
        # Build system message
        system_content = ("You are a helpful assistant that answers questions based on provided context. "
                         "Each source includes location information in brackets. "
                         "When referencing information, mention the specific location (page, section) when available. "
                         "If the context doesn't contain enough information to answer the question, "
                         "say so clearly. Always be accurate and cite the information from the context.")
        
        if conversation_history:
            system_content += (" You also have access to recent conversation history to understand "
                             "context and references like 'it', 'that', 'the previous topic', etc.")
        
        # Build user message
        user_content = f"Context with location information:\n{context}"
        
        if conversation_history:
            user_content += f"\n\nRecent Conversation:\n{conversation_history}"
        
        user_content += f"\n\nQuestion: {query}\n\nAnswer the question and reference specific locations when mentioning information:"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        return self.clients.openai.generate_response(messages)
    
    def search_with_paragraphs(self, query: str, top_k_paragraphs: int = 3, top_k_chunks: int = 5, conversation_history: str = "") -> ChatResponse:
        """Search using paragraph summaries for wider context plus detailed chunks"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing query with paragraph context: {query}")
            
            # Get detailed chunk search
            chunk_response = self.search_and_answer(query, top_k_chunks, conversation_history)
            
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
            enhanced_answer = self._generate_paragraph_aware_answer(query, combined_context, conversation_history)
            
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
            return self.search_and_answer(query, top_k_chunks, conversation_history)
    
    def _generate_paragraph_aware_answer(self, query: str, combined_context: str, conversation_history: str = "") -> str:
        """Generate answer using both paragraph context and detailed chunks with optional conversation history"""
        
        # Build system message
        system_content = ("Use both detailed information and wider paragraph context to provide comprehensive answers. "
                         "Paragraph summaries give broader context and themes, detailed information provides specific facts.")
        
        if conversation_history:
            system_content += (" You also have access to recent conversation history to understand "
                             "context and references like 'it', 'that', 'the previous topic', etc.")
        
        # Build user message
        user_content = f"Context:\n{combined_context}"
        
        if conversation_history:
            user_content += f"\n\nRecent Conversation:\n{conversation_history}"
        
        user_content += f"\n\nQuestion: {query}\n\nAnswer using both the detailed information and broader paragraph context:"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        return self.clients.openai.generate_response(messages)