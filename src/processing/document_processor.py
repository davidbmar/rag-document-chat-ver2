#!/usr/bin/env python3
"""
Document processing module for RAG Document Chat System
"""

import io
import time
import logging
from pathlib import Path
from typing import List, Tuple

try:
    import PyPDF2
except ImportError:
    import pypdf as PyPDF2

from core.models import DocumentResponse, ChunkMetadata
from processing.text_processing import EnhancedDocumentProcessor
from core.clients import ClientManager

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extract text from various document formats"""
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from uploaded files"""
        file_ext = Path(filename).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_pdf_text(file_content)
            elif file_ext == '.txt':
                return self._extract_txt_text(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            raise
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        
        for page_num, page in enumerate(reader.pages):
            try:
                text += page.extract_text() + "\n"
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
        
        return text.strip()
    
    def _extract_txt_text(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            return file_content.decode('utf-8', errors='ignore')


class DocumentProcessor:
    """Main document processor orchestrating all processing steps"""
    
    def __init__(self, client_manager: ClientManager):
        self.clients = client_manager
        self.extractor = DocumentExtractor()
        self.text_processor = EnhancedDocumentProcessor()
        
        # Get collections
        self.document_collection = self.clients.chromadb.get_or_create_collection(
            "documents",
            {"description": "RAG document collection"}
        )
        
        self.original_text_collection = self.clients.chromadb.get_or_create_collection(
            "original_texts",
            {"description": "Original document texts for hierarchical processing"}
        )
    
    async def process_document(self, file_content: bytes, filename: str) -> DocumentResponse:
        """Process uploaded document: extract text, chunk, embed, and store"""
        start_time = time.time()
        
        try:
            logger.info(f"📄 Processing document: {filename}")
            
            # Extract text
            text = self.extractor.extract_text(file_content, filename)
            if not text.strip():
                return DocumentResponse(
                    status="error",
                    message="No text content found in document",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"📝 Extracted {len(text)} characters")
            
            # Store original text for hierarchical processing
            self._store_original_text(text, filename)
            
            # Upload to S3 if configured
            if self.clients.s3.client:
                self.clients.s3.upload_file(file_content, filename)
            
            # Process text into chunks with metadata
            chunks_with_metadata = self.text_processor.process_document_with_metadata(text, filename)
            
            if not chunks_with_metadata:
                return DocumentResponse(
                    status="error",
                    message="Failed to create text chunks",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"✂️ Created {len(chunks_with_metadata)} logical chunks")
            
            # Generate embeddings and store
            chunks_stored = await self._store_chunks(chunks_with_metadata)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Successfully processed {filename} in {processing_time:.2f}s")
            
            return DocumentResponse(
                status="success",
                message=f"Successfully processed {chunks_stored} logical chunks",
                chunks_created=chunks_stored,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return DocumentResponse(
                status="error",
                message=f"Processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _store_chunks(self, chunks_with_metadata: List[Tuple[str, ChunkMetadata]]) -> int:
        """Store chunks with embeddings in ChromaDB"""
        stored_count = 0
        
        for chunk_text, metadata in chunks_with_metadata:
            try:
                embedding = self.clients.openai.get_embedding(chunk_text)
                chunk_id = f"{metadata.filename}_{metadata.chunk_index}_{metadata.chunk_hash}"
                
                self.document_collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk_text],
                    metadatas=[self.text_processor.create_metadata_dict(metadata)]
                )
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process chunk {metadata.chunk_index}: {e}")
                continue
        
        return stored_count
    
    def _store_original_text(self, text: str, filename: str):
        """Store original document text for later hierarchical processing"""
        try:
            # Use a dummy embedding for storage
            simple_embedding = [0.0] * 1536
            
            self.original_text_collection.add(
                ids=[f"fulltext_{filename}"],
                embeddings=[simple_embedding],
                documents=[text],
                metadatas=[{
                    "filename": filename,
                    "content_type": "original_text",
                    "character_count": len(text),
                    "word_count": len(text.split())
                }]
            )
            
            logger.info(f"✅ Stored original text for {filename}")
            
        except Exception as e:
            logger.error(f"Failed to store original text: {e}")