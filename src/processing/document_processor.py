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

# Import PyMuPDF if available
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from src.core.models import DocumentResponse, ChunkMetadata
from src.processing.text_processing import EnhancedDocumentProcessor
from src.core.clients import ClientManager
from src.core.config import config

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
        """Extract text from PDF using configured library"""
        pdf_library = config.pdf_library.lower()
        
        logger.info(f"🔧 PDF extraction config: PDF_LIBRARY={pdf_library}")
        logger.info(f"📚 PyMuPDF available: {HAS_PYMUPDF}")
        
        # Try PyMuPDF first if configured and available
        if pdf_library == "pymupdf" and HAS_PYMUPDF:
            logger.info("🚀 Using PyMuPDF for PDF extraction")
            try:
                return self._extract_pdf_with_pymupdf(file_content)
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed, falling back to PyPDF2: {e}")
                return self._extract_pdf_with_pypdf2(file_content)
        
        # Use PyPDF2 as default or fallback
        elif pdf_library == "pypdf2" or not HAS_PYMUPDF:
            if pdf_library == "pymupdf" and not HAS_PYMUPDF:
                logger.warning("⚠️ PyMuPDF requested but not installed, using PyPDF2")
            else:
                logger.info("🔧 Using PyPDF2 for PDF extraction")
            return self._extract_pdf_with_pypdf2(file_content)
        
        else:
            logger.warning(f"Unknown PDF library '{pdf_library}', using PyPDF2")
            return self._extract_pdf_with_pypdf2(file_content)
    
    def _extract_pdf_with_pymupdf(self, file_content: bytes) -> str:
        """Extract text from PDF using PyMuPDF (fitz)"""
        text = ""
        
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num} with PyMuPDF: {e}")
            
            doc.close()
            logger.info(f"✅ Successfully extracted text with PyMuPDF ({len(text)} chars)")
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
        
        return text.strip()
    
    def _extract_pdf_with_pypdf2(self, file_content: bytes) -> str:
        """Extract text from PDF using PyPDF2"""
        text = ""
        
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num} with PyPDF2: {e}")
            
            logger.info(f"✅ Successfully extracted text with PyPDF2 ({len(text)} chars)")
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
        
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