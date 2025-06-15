#!/usr/bin/env python3
"""
Data models for RAG Document Chat System
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str
    top_k: int = 15


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str
    sources: List[str]
    processing_time: float


class DocumentResponse(BaseModel):
    """Response model for document processing"""
    status: str
    message: str
    chunks_created: int = 0
    processing_time: float = 0.0


@dataclass
class ChunkMetadata:
    """Enhanced metadata for document chunks"""
    filename: str
    chunk_index: int
    total_chunks: int
    chunk_size: int
    chunk_summary: str
    page_number: Optional[int]
    section_title: Optional[str]
    start_char: int
    end_char: int
    paragraph_number: int
    content_type: str
    key_terms: List[str]
    chunk_hash: str


@dataclass
class LogicalGroup:
    """A group of sentences that represent a single logical idea"""
    group_id: str
    sentences: List[str]
    combined_text: str
    topic_indicators: List[str]
    word_count: int
    coherence_score: float


@dataclass
class CompressedGroup:
    """A logical group with its compressed summary"""
    original_group: LogicalGroup
    summary: str
    compression_ratio: float
    strategy_used: str
    processing_time: float


@dataclass
class HierarchicalResult:
    """Result of hierarchical processing"""
    status: str
    message: str
    filename: str
    logical_groups_created: int
    summaries_created: int
    total_processing_time: float
    compression_stats: Dict
    groups: List[CompressedGroup]


class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str
    top_k: int = 10
    collections: Optional[List[str]] = None  # Filter by collection names
    documents: Optional[List[str]] = None    # Filter by document filenames
    exclude_documents: Optional[List[str]] = None  # Exclude specific documents
    threshold: Optional[float] = None        # Minimum similarity score
    return_chunks: bool = True               # Include chunk IDs in response


class SearchResult(BaseModel):
    """Individual search result"""
    content: str
    score: float
    document: str
    chunk_id: str
    collection: str
    metadata: Dict


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    results: List[SearchResult]
    search_id: str                          # Unique ID for this search
    query: str
    total_results: int
    unique_documents: List[str]             # List of unique document names
    chunk_ids: List[str]                    # List of all chunk IDs found
    processing_time: float
    collections_searched: List[str]


class AskRequest(BaseModel):
    """Enhanced request model for ask endpoint"""
    question: str
    top_k: int = 8
    documents: Optional[List[str]] = None           # Filter to specific documents
    exclude_documents: Optional[List[str]] = None  # Exclude specific documents
    chunk_ids: Optional[List[str]] = None          # Use specific chunks only
    search_id: Optional[str] = None                # Use previous search results
    conversation_history: Optional[str] = ""
    search_strategy: Optional[str] = "enhanced"    # basic, enhanced, paragraph


class ProcessRequest(BaseModel):
    """Request model for document processing"""
    filename: str
    process_type: str  # "basic", "summaries", "paragraphs"