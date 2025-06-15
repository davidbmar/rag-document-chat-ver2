#!/usr/bin/env python3
"""
Paragraph-based processing for wider context search
"""

import asyncio
import time
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from core.models import DocumentResponse
from core.clients import ClientManager

logger = logging.getLogger(__name__)


@dataclass
class ParagraphSummary:
    """A paragraph with its AI-generated summary"""
    paragraph_id: str
    original_text: str
    summary: str
    word_count: int
    summary_word_count: int
    compression_ratio: float
    paragraph_index: int
    total_paragraphs: int
    processing_time: float


@dataclass
class ParagraphProcessingResult:
    """Result of paragraph processing"""
    status: str
    message: str
    filename: str
    paragraphs_processed: int
    summaries_created: int
    total_processing_time: float
    compression_stats: Dict
    paragraphs: List[ParagraphSummary]


class ParagraphProcessor:
    """Process documents at paragraph level for wider context search"""
    
    def __init__(self, client_manager: ClientManager):
        self.clients = client_manager
        
        # Create collection for paragraph summaries
        try:
            self.paragraph_collection = self.clients.chromadb.get_or_create_collection(
                "paragraph_summaries",
                {"description": "Paragraph-level summaries for wider context search"}
            )
        except Exception as e:
            logger.error(f"Failed to create paragraph collection: {e}")
            self.paragraph_collection = None
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs using natural paragraph breaks"""
        # Split on double newlines (paragraph breaks)
        paragraphs = text.split('\n\n')
        
        # Clean and filter paragraphs
        clean_paragraphs = []
        for para in paragraphs:
            # Clean whitespace and normalize
            para = para.strip()
            para = ' '.join(para.split())  # Normalize internal whitespace
            
            # Filter out very short paragraphs (likely not meaningful content)
            if len(para) > 50:  # At least 50 characters
                clean_paragraphs.append(para)
        
        return clean_paragraphs
    
    async def summarize_paragraph(self, paragraph: str, target_length: int = 50) -> str:
        """Create a summary of a paragraph using GPT"""
        
        # Don't summarize if already short
        word_count = len(paragraph.split())
        if word_count <= target_length:
            return paragraph
        
        prompt = f"""
        Summarize this paragraph in exactly {target_length} words or less while preserving the key information and main ideas.
        
        Requirements:
        - Keep the most important information
        - Maintain searchable keywords
        - Preserve proper nouns and key concepts
        - Write in clear, concise language
        
        Paragraph:
        {paragraph}
        
        Summary ({target_length} words max):"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert at creating {target_length}-word paragraph summaries that preserve essential information."
                },
                {"role": "user", "content": prompt}
            ]
            
            summary = await asyncio.to_thread(
                self.clients.openai.generate_response,
                messages,
                0.1,
                target_length * 2
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Paragraph summarization failed: {e}")
            # Fallback: truncate to target length
            words = paragraph.split()
            return ' '.join(words[:target_length]) + "..."
    
    async def process_document_paragraphs(self, filename: str) -> ParagraphProcessingResult:
        """Process a document into paragraph summaries"""
        start_time = time.time()
        
        try:
            logger.info(f"📄 Starting paragraph processing for: {filename}")
            
            # Get original document text from ChromaDB
            text = await self.get_document_text(filename)
            if not text:
                return ParagraphProcessingResult(
                    status="error",
                    message=f"Could not find document text for {filename}",
                    filename=filename,
                    paragraphs_processed=0,
                    summaries_created=0,
                    total_processing_time=time.time() - start_time,
                    compression_stats={},
                    paragraphs=[]
                )
            
            # Split into paragraphs
            paragraphs = self.split_into_paragraphs(text)
            logger.info(f"📝 Found {len(paragraphs)} paragraphs")
            
            if not paragraphs:
                return ParagraphProcessingResult(
                    status="error",
                    message="No paragraphs found in document",
                    filename=filename,
                    paragraphs_processed=0,
                    summaries_created=0,
                    total_processing_time=time.time() - start_time,
                    compression_stats={},
                    paragraphs=[]
                )
            
            # Process each paragraph
            processed_paragraphs = []
            total_input_words = 0
            total_output_words = 0
            
            for i, paragraph in enumerate(paragraphs):
                para_start_time = time.time()
                
                # Calculate target summary length (aim for 3:1 compression)
                word_count = len(paragraph.split())
                target_length = max(15, min(50, word_count // 3))
                
                # Generate summary
                summary = await self.summarize_paragraph(paragraph, target_length)
                summary_word_count = len(summary.split())
                
                # Create paragraph summary object
                para_summary = ParagraphSummary(
                    paragraph_id=f"{filename}_para_{i}",
                    original_text=paragraph,
                    summary=summary,
                    word_count=word_count,
                    summary_word_count=summary_word_count,
                    compression_ratio=word_count / summary_word_count if summary_word_count > 0 else 1.0,
                    paragraph_index=i,
                    total_paragraphs=len(paragraphs),
                    processing_time=time.time() - para_start_time
                )
                
                processed_paragraphs.append(para_summary)
                total_input_words += word_count
                total_output_words += summary_word_count
                
                logger.info(f"📄 Processed paragraph {i+1}/{len(paragraphs)} ({word_count} → {summary_word_count} words)")
            
            # Store paragraph summaries in ChromaDB
            summaries_stored = await self.store_paragraph_summaries(processed_paragraphs, filename)
            
            # Calculate overall stats
            overall_ratio = total_input_words / total_output_words if total_output_words > 0 else 1.0
            compression_stats = {
                'total_input_words': total_input_words,
                'total_output_words': total_output_words,
                'overall_compression_ratio': overall_ratio,
                'average_paragraph_size': total_input_words / len(paragraphs) if paragraphs else 0,
                'average_summary_size': total_output_words / len(paragraphs) if paragraphs else 0
            }
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Paragraph processing complete: {len(paragraphs)} paragraphs, {overall_ratio:.1f}:1 compression")
            
            return ParagraphProcessingResult(
                status="success",
                message=f"Processed {len(paragraphs)} paragraphs with {overall_ratio:.1f}:1 compression",
                filename=filename,
                paragraphs_processed=len(paragraphs),
                summaries_created=summaries_stored,
                total_processing_time=processing_time,
                compression_stats=compression_stats,
                paragraphs=processed_paragraphs
            )
            
        except Exception as e:
            logger.error(f"Paragraph processing failed: {e}")
            return ParagraphProcessingResult(
                status="error",
                message=f"Processing failed: {str(e)}",
                filename=filename,
                paragraphs_processed=0,
                summaries_created=0,
                total_processing_time=time.time() - start_time,
                compression_stats={},
                paragraphs=[]
            )
    
    async def get_document_text(self, filename: str) -> Optional[str]:
        """Retrieve original document text from original_texts collection"""
        try:
            # Get original texts collection
            text_collection = self.clients.chromadb.get_or_create_collection(
                "original_texts",
                {"description": "Original document texts"}
            )
            
            # Query for the specific document
            results = text_collection.get(
                where={"filename": filename},
                limit=1
            )
            
            if results['documents']:
                return results['documents'][0]
            else:
                logger.error(f"No original text found for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve document text: {e}")
            return None
    
    async def store_paragraph_summaries(self, paragraphs: List[ParagraphSummary], filename: str) -> int:
        """Store paragraph summaries in ChromaDB"""
        
        if not self.paragraph_collection:
            return 0
        
        stored_count = 0
        
        try:
            for paragraph in paragraphs:
                # Generate embedding for the summary
                embedding = self.clients.openai.get_embedding(paragraph.summary)
                
                self.paragraph_collection.add(
                    ids=[paragraph.paragraph_id],
                    embeddings=[embedding],
                    documents=[paragraph.summary],
                    metadatas=[{
                        "filename": filename,
                        "paragraph_index": paragraph.paragraph_index,
                        "total_paragraphs": paragraph.total_paragraphs,
                        "content_type": "paragraph_summary",
                        "original_words": paragraph.word_count,
                        "summary_words": paragraph.summary_word_count,
                        "compression_ratio": paragraph.compression_ratio,
                        "original_text": paragraph.original_text[:500] + "..." if len(paragraph.original_text) > 500 else paragraph.original_text
                    }]
                )
                stored_count += 1
                
        except Exception as e:
            logger.error(f"Failed to store paragraph summaries: {e}")
        
        return stored_count
    
    def search_paragraphs(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search paragraph summaries for relevant content"""
        
        if not self.paragraph_collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.clients.openai.get_embedding(query)
            
            # Search paragraph summaries
            results = self.paragraph_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            paragraph_results = []
            if results['documents'][0]:
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    paragraph_results.append({
                        'summary': doc,
                        'filename': metadata['filename'],
                        'paragraph_index': metadata['paragraph_index'],
                        'original_text': metadata.get('original_text', ''),
                        'compression_ratio': metadata.get('compression_ratio', 1.0),
                        'relevance_score': 1.0 - (i * 0.1)  # Simple relevance scoring
                    })
            
            return paragraph_results
            
        except Exception as e:
            logger.error(f"Paragraph search failed: {e}")
            return []