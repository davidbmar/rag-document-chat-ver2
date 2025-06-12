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