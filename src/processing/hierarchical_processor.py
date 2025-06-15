#!/usr/bin/env python3
"""
hierarchical_processor.py
Enhanced RAG processing with logical grouping and 10:1 compression summaries
"""

import asyncio
import time
import re
import logging
from typing import List, Dict, Tuple, Optional
try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    nltk = None

from src.core.models import LogicalGroup, CompressedGroup, HierarchicalResult, ChatResponse
from src.core.clients import ClientManager

logger = logging.getLogger(__name__)

class SemanticSentenceGrouper:
    """Groups sentences into logical idea units"""
    
    def __init__(self):
        # Discourse markers that indicate topic shifts
        self.topic_shift_markers = {
            'contrast': ['however', 'but', 'although', 'nevertheless', 'on the other hand'],
            'sequence': ['first', 'second', 'next', 'then', 'finally', 'meanwhile'],
            'causation': ['because', 'therefore', 'as a result', 'consequently', 'thus'],
            'addition': ['furthermore', 'moreover', 'additionally', 'also', 'besides'],
            'time': ['suddenly', 'immediately', 'later', 'soon', 'eventually'],
            'dialogue': ['said', 'asked', 'replied', 'exclaimed', 'whispered', 'shouted']
        }
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into clean sentences"""
        if NLTK_AVAILABLE:
            sentences = nltk.sent_tokenize(text)
        else:
            # Simple fallback
            sentences = [s.strip() for s in text.split('.') if s.strip()]
        clean_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter very short sentences
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    def detect_topic_shift(self, sentence: str) -> bool:
        """Detect if sentence indicates a topic shift"""
        sentence_lower = sentence.lower()
        
        # Check for discourse markers
        for category, markers in self.topic_shift_markers.items():
            for marker in markers:
                if sentence_lower.startswith(marker) or f" {marker} " in sentence_lower:
                    return True
        
        # Check for other shift patterns
        shift_patterns = [
            r'^(suddenly|immediately|meanwhile|later)',
            r'^(alice then|alice now|alice decided)',
            r'(chapter \d+|section \d+)'
        ]
        
        for pattern in shift_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        return False
    
    def calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate semantic similarity between sentences"""
        words1 = set(sent1.lower().split())
        words2 = set(sent2.lower().split())
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        return overlap / total if total > 0 else 0
    
    def group_sentences_by_similarity(self, sentences: List[str], similarity_threshold: float = 0.3) -> List[LogicalGroup]:
        """Group sentences based on semantic similarity"""
        
        if not sentences:
            return []
        
        groups = []
        current_group = [sentences[0]]
        group_index = 0
        
        for i in range(1, len(sentences)):
            current_sentence = sentences[i]
            should_break = False
            
            # Check for topic shift
            if self.detect_topic_shift(current_sentence):
                should_break = True
            
            # Check similarity with current group
            elif current_group:
                similarity = self.calculate_sentence_similarity(current_group[-1], current_sentence)
                if similarity < similarity_threshold:
                    should_break = True
            
            # Check group size (max ~150 words)
            elif len(' '.join(current_group).split()) > 150:
                should_break = True
            
            if should_break and current_group:
                group = self.create_logical_group(current_group, group_index)
                groups.append(group)
                current_group = [current_sentence]
                group_index += 1
            else:
                current_group.append(current_sentence)
        
        # Add final group
        if current_group:
            group = self.create_logical_group(current_group, group_index)
            groups.append(group)
        
        return groups
    
    def create_logical_group(self, sentences: List[str], group_index: int) -> LogicalGroup:
        """Create a LogicalGroup from sentences"""
        combined_text = ' '.join(sentences)
        word_count = len(combined_text.split())
        
        # Simple coherence calculation
        coherence_score = 1.0 if len(sentences) == 1 else 0.7  # Simplified
        
        return LogicalGroup(
            group_id=f"group_{group_index}",
            sentences=sentences,
            combined_text=combined_text,
            topic_indicators=[],  # Could be enhanced
            word_count=word_count,
            coherence_score=coherence_score
        )
    
    def process_text_into_groups(self, text: str) -> List[LogicalGroup]:
        """Main method: split text into logical groups"""
        sentences = self.split_into_sentences(text)
        groups = self.group_sentences_by_similarity(sentences)
        
        logger.info(f"📝 Grouped {len(sentences)} sentences into {len(groups)} logical units")
        return groups

class AdaptiveCompressor:
    """Compresses logical groups with 10:1 target ratio"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    def choose_compression_strategy(self, text: str, word_count: int) -> str:
        """Choose compression strategy based on content"""
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in ['steps', 'procedure', 'method', 'process']):
            return 'detailed'  # 8:1 ratio
        elif any(indicator in text_lower for indicator in ['list', 'including', 'such as']):
            return 'balanced'  # 10:1 ratio
        else:
            return 'balanced'  # Default 10:1
    
    def calculate_target_length(self, input_length: int, strategy: str) -> int:
        """Calculate target summary length"""
        ratios = {
            'detailed': 8.0,   # 8:1
            'balanced': 10.0,  # 10:1 (your target)
            'aggressive': 15.0 # 15:1
        }
        
        ratio = ratios.get(strategy, 10.0)
        target = int(input_length / ratio)
        
        # Reasonable bounds
        return max(10, min(50, target))
    
    async def compress_logical_group(self, group: LogicalGroup) -> CompressedGroup:
        """Compress a logical group with 10:1 ratio"""
        start_time = time.time()
        
        # Skip very short groups
        if group.word_count < 40:
            return CompressedGroup(
                original_group=group,
                summary=group.combined_text,
                compression_ratio=1.0,
                strategy_used='no_compression',
                processing_time=time.time() - start_time
            )
        
        strategy = self.choose_compression_strategy(group.combined_text, group.word_count)
        target_length = self.calculate_target_length(group.word_count, strategy)
        
        prompt = f"""
        Compress this text to exactly {target_length} words while preserving key information and searchable content.

        Requirements:
        - Target: {target_length} words (10:1 compression from {group.word_count} words)
        - Keep proper names, character names, and important details
        - Preserve the main topic and key events
        - Make it useful for search and retrieval

        Original text:
        {group.combined_text}

        Compressed summary ({target_length} words):"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert at creating {target_length}-word summaries that preserve essential information for search."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_text = await asyncio.to_thread(
                self.openai_client.generate_response,
                messages,
                0.1,
                target_length * 3
            )
            
            summary = response_text.strip()
            summary_words = len(summary.split())
            compression_ratio = group.word_count / summary_words if summary_words > 0 else 1.0
            
            return CompressedGroup(
                original_group=group,
                summary=summary,
                compression_ratio=compression_ratio,
                strategy_used=strategy,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Fallback to simple truncation
            words = group.combined_text.split()
            fallback_summary = ' '.join(words[:target_length]) + "..."
            
            return CompressedGroup(
                original_group=group,
                summary=fallback_summary,
                compression_ratio=group.word_count / target_length,
                strategy_used='fallback',
                processing_time=time.time() - start_time
            )

class HierarchicalProcessor:
    """Main processor that coordinates grouping and compression"""
    
    def __init__(self, client_manager: ClientManager):
        self.clients = client_manager
        self.grouper = SemanticSentenceGrouper()
        self.compressor = AdaptiveCompressor(client_manager.openai)
        
        # Get collections
        self.document_collection = self.clients.chromadb.get_or_create_collection(
            "documents",
            {"description": "RAG document collection"}
        )
        
        self.summary_collection = self.clients.chromadb.get_or_create_collection(
            "logical_summaries",
            {"description": "10:1 compressed summaries of logical groups"}
        )
    
    async def process_document_hierarchically(self, filename: str) -> HierarchicalResult:
        """Process an already-uploaded document with hierarchical compression"""
        start_time = time.time()
        
        try:
            logger.info(f"🧠 Starting hierarchical processing for: {filename}")
            
            text = await self.get_document_text(filename)
            if not text:
                return HierarchicalResult(
                    status="error",
                    message=f"Could not find document text for {filename}",
                    filename=filename,
                    logical_groups_created=0,
                    summaries_created=0,
                    total_processing_time=time.time() - start_time,
                    compression_stats={},
                    groups=[]
                )
            
            # Step 1: Create logical groups
            logical_groups = self.grouper.process_text_into_groups(text)
            logger.info(f"📝 Created {len(logical_groups)} logical groups")
            
            # Step 2: Compress each group
            compressed_groups = []
            total_input_words = 0
            total_output_words = 0
            
            for group in logical_groups:
                compressed = await self.compressor.compress_logical_group(group)
                compressed_groups.append(compressed)
                
                total_input_words += group.word_count
                total_output_words += len(compressed.summary.split())
            
            # Step 3: Store summaries in ChromaDB
            summaries_stored = await self.store_summaries(compressed_groups, filename)
            
            # Calculate stats
            overall_ratio = total_input_words / total_output_words if total_output_words > 0 else 1.0
            compression_stats = {
                'total_input_words': total_input_words,
                'total_output_words': total_output_words,
                'overall_compression_ratio': overall_ratio,
                'average_group_size': total_input_words / len(logical_groups) if logical_groups else 0
            }
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Hierarchical processing complete: {len(logical_groups)} groups, {overall_ratio:.1f}:1 compression")
            
            return HierarchicalResult(
                status="success",
                message=f"Created {len(logical_groups)} logical groups with {overall_ratio:.1f}:1 compression",
                filename=filename,
                logical_groups_created=len(logical_groups),
                summaries_created=summaries_stored,
                total_processing_time=processing_time,
                compression_stats=compression_stats,
                groups=compressed_groups
            )
            
        except Exception as e:
            logger.error(f"Hierarchical processing failed: {e}")
            return HierarchicalResult(
                status="error",
                message=f"Processing failed: {str(e)}",
                filename=filename,
                logical_groups_created=0,
                summaries_created=0,
                total_processing_time=time.time() - start_time,
                compression_stats={},
                groups=[]
            )
    
    async def get_document_text(self, filename: str) -> Optional[str]:
        """Retrieve original document text from ChromaDB chunks"""
        try:
            results = self.document_collection.get(
                where={"filename": filename},
                limit=2000
            )
            
            if not results['documents']:
                return None
            
            # Combine all chunks back into original text
            chunks = results['documents']
            metadatas = results['metadatas']
            
            # Sort by chunk index to maintain order
            chunk_data = [(chunk, meta.get('chunk_index', 0)) for chunk, meta in zip(chunks, metadatas)]
            chunk_data.sort(key=lambda x: x[1])
            
            # Combine chunks
            full_text = ' '.join([chunk for chunk, _ in chunk_data])
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to retrieve document text: {e}")
            return None
    
    async def store_summaries(self, compressed_groups: List[CompressedGroup], filename: str) -> int:
        """Store compressed summaries in ChromaDB"""
        
        if not self.summary_collection:
            return 0
        
        stored_count = 0
        
        try:
            for compressed in compressed_groups:
                embedding = self.clients.openai.get_embedding(compressed.summary)
                
                self.summary_collection.add(
                    ids=[f"{filename}_{compressed.original_group.group_id}"],
                    embeddings=[embedding],
                    documents=[compressed.summary],
                    metadatas=[{
                        "filename": filename,
                        "group_id": compressed.original_group.group_id,
                        "content_type": "logical_summary",
                        "original_words": compressed.original_group.word_count,
                        "summary_words": len(compressed.summary.split()),
                        "compression_ratio": compressed.compression_ratio,
                        "strategy_used": compressed.strategy_used
                    }]
                )
                stored_count += 1
                
        except Exception as e:
            logger.error(f"Failed to store summaries: {e}")
        
        return stored_count
    
    def search_with_summaries(self, query: str, top_k_summaries: int = 5, top_k_chunks: int = 3) -> ChatResponse:
        """Search using both summaries and original chunks"""
        
        from src.search.search_engine import SearchEngine
        search_engine = SearchEngine(self.clients)
        
        return search_engine.search_enhanced(query, top_k_chunks, use_summaries=True)
