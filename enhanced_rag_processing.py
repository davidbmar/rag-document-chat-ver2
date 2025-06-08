#!/usr/bin/env python3
"""
Enhanced RAG Document Processing with Chunk Summaries and Better Indexing
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

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

class EnhancedDocumentProcessor:
    """Enhanced document processor with better chunk metadata"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_page_numbers(self, text: str) -> Dict[int, int]:
        """Extract page numbers and their positions in text"""
        page_positions = {}
        # Look for page indicators (adjust regex based on your documents)
        page_patterns = [
            r'Page\s+(\d+)',
            r'page\s+(\d+)',
            r'\[Page\s+(\d+)\]',
            r'(?:^|\n)\s*(\d+)\s*(?:\n|$)'  # Standalone numbers
        ]
        
        for pattern in page_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                page_num = int(match.group(1))
                position = match.start()
                page_positions[position] = page_num
        
        return page_positions
    
    def extract_section_titles(self, text: str) -> Dict[int, str]:
        """Extract section titles and their positions"""
        section_positions = {}
        
        # Common patterns for section headers
        patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]{2,})$',  # ALL CAPS headers
            r'^\d+\.\s+(.+)$',  # Numbered sections
            r'^Chapter\s+\d+:?\s*(.*)$',  # Chapter headers
            r'^\*\*(.+)\*\*$'  # Bold headers
        ]
        
        lines = text.split('\n')
        char_position = 0
        
        for line in lines:
            line_stripped = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 3:  # Filter out very short "titles"
                        section_positions[char_position] = title
                    break
            char_position += len(line) + 1  # +1 for newline
        
        return section_positions
    
    def get_page_number_for_position(self, position: int, page_positions: Dict[int, int]) -> Optional[int]:
        """Get page number for a given character position"""
        if not page_positions:
            return None
        
        # Find the last page number before or at this position
        relevant_pages = [(pos, page) for pos, page in page_positions.items() if pos <= position]
        if relevant_pages:
            return max(relevant_pages, key=lambda x: x[0])[1]
        return None
    
    def get_section_title_for_position(self, position: int, section_positions: Dict[int, str]) -> Optional[str]:
        """Get section title for a given character position"""
        if not section_positions:
            return None
        
        # Find the last section title before or at this position
        relevant_sections = [(pos, title) for pos, title in section_positions.items() if pos <= position]
        if relevant_sections:
            return max(relevant_sections, key=lambda x: x[0])[1]
        return None
    
    def generate_chunk_summary(self, chunk_text: str, max_length: int = 120) -> str:
        """Generate a concise summary of the chunk content"""
        # Clean the text
        clean_text = re.sub(r'\s+', ' ', chunk_text.strip())
        
        # Extract first meaningful sentence
        sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 10]
        
        if sentences:
            summary = sentences[0]
            # If first sentence is too short, add second sentence
            if len(summary) < 50 and len(sentences) > 1:
                summary += ". " + sentences[1]
        else:
            # Fallback to first N characters
            summary = clean_text[:max_length]
        
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def extract_key_terms(self, chunk_text: str, max_terms: int = 5) -> List[str]:
        """Extract key terms from chunk text"""
        # Simple approach - extract capitalized words and important terms
        text = re.sub(r'[^\w\s]', ' ', chunk_text)
        words = text.split()
        
        # Find capitalized words (potential proper nouns/important terms)
        capitalized = [w for w in words if w[0].isupper() and len(w) > 2]
        
        # Find longer words (likely important)
        long_words = [w.lower() for w in words if len(w) > 6]
        
        # Combine and deduplicate
        key_terms = list(set(capitalized + long_words))
        
        # Sort by frequency in text and return top terms
        term_freq = {term: chunk_text.lower().count(term.lower()) for term in key_terms}
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [term for term, freq in sorted_terms[:max_terms]]
    
    def determine_content_type(self, chunk_text: str) -> str:
        """Determine the type of content in the chunk"""
        text_lower = chunk_text.lower()
        
        # Check for various content types
        if re.search(r'\d+\.\s+.*\d+\.\s+.*\d+\.\s+', chunk_text):
            return "numbered_list"
        elif re.search(r'[•\-\*]\s+.*[•\-\*]\s+', chunk_text):
            return "bullet_list"
        elif re.search(r'(table|column|row)', text_lower):
            return "table_content"
        elif re.search(r'(figure|chart|graph|image)', text_lower):
            return "figure_reference"
        elif re.search(r'(introduction|overview|summary|conclusion)', text_lower):
            return "summary_content"
        elif re.search(r'(step|procedure|method|process)', text_lower):
            return "procedural"
        elif chunk_text.count('?') > 2:
            return "faq_content"
        else:
            return "general_text"
    
    def calculate_chunk_hash(self, chunk_text: str) -> str:
        """Calculate hash for chunk deduplication"""
        return hashlib.md5(chunk_text.encode()).hexdigest()[:12]
    
    def count_paragraphs_before_position(self, text: str, position: int) -> int:
        """Count paragraphs before given position"""
        text_before = text[:position]
        return text_before.count('\n\n') + 1
    
    def process_document_with_enhanced_metadata(self, text: str, filename: str) -> List[Tuple[str, ChunkMetadata]]:
        """Process document and create enhanced metadata for each chunk"""
        
        # Pre-analyze document structure
        page_positions = self.extract_page_numbers(text)
        section_positions = self.extract_section_titles(text)
        
        # Split into chunks with position tracking
        chunks = []
        current_position = 0
        
        # Use text splitter to get chunks
        text_chunks = self.text_splitter.split_text(text)
        
        for i, chunk_text in enumerate(text_chunks):
            # Find this chunk's position in original text
            chunk_start = text.find(chunk_text, current_position)
            if chunk_start == -1:
                # Fallback if exact match not found
                chunk_start = current_position
            
            chunk_end = chunk_start + len(chunk_text)
            current_position = chunk_end
            
            # Generate enhanced metadata
            metadata = ChunkMetadata(
                filename=filename,
                chunk_index=i,
                total_chunks=len(text_chunks),
                chunk_size=len(chunk_text),
                chunk_summary=self.generate_chunk_summary(chunk_text),
                page_number=self.get_page_number_for_position(chunk_start, page_positions),
                section_title=self.get_section_title_for_position(chunk_start, section_positions),
                start_char=chunk_start,
                end_char=chunk_end,
                paragraph_number=self.count_paragraphs_before_position(text, chunk_start),
                content_type=self.determine_content_type(chunk_text),
                key_terms=self.extract_key_terms(chunk_text),
                chunk_hash=self.calculate_chunk_hash(chunk_text)
            )
            
            chunks.append((chunk_text, metadata))
        
        return chunks
    
    def create_searchable_metadata_dict(self, metadata: ChunkMetadata) -> Dict:
        """Convert metadata to dictionary for ChromaDB storage"""
        return {
            "filename": metadata.filename,
            "chunk_index": metadata.chunk_index,
            "total_chunks": metadata.total_chunks,
            "chunk_size": metadata.chunk_size,
            "chunk_summary": metadata.chunk_summary,
            "page_number": metadata.page_number,
            "section_title": metadata.section_title or "Unknown Section",
            "start_char": metadata.start_char,
            "end_char": metadata.end_char,
            "paragraph_number": metadata.paragraph_number,
            "content_type": metadata.content_type,
            "key_terms": ", ".join(metadata.key_terms),
            "chunk_hash": metadata.chunk_hash,
            "location_reference": f"Page {metadata.page_number or 'N/A'}, Section: {metadata.section_title or 'Unknown'}, Paragraph {metadata.paragraph_number}"
        }

# Enhanced search and answer functionality
class EnhancedRAGSystem:
    """Enhanced RAG system with better metadata and summaries"""
    
    def __init__(self, rag_system):
        self.base_system = rag_system
        self.processor = EnhancedDocumentProcessor(rag_system.openai_client)
    
    async def process_document_enhanced(self, file_content: bytes, filename: str):
        """Process document with enhanced metadata"""
        start_time = time.time()
        
        try:
            # Extract text (reuse existing method)
            text = self.base_system.extract_text(file_content, filename)
            if not text.strip():
                return DocumentResponse(
                    status="error",
                    message="No text content found in document",
                    processing_time=time.time() - start_time
                )
            
            # Process with enhanced metadata
            chunks_with_metadata = self.processor.process_document_with_enhanced_metadata(text, filename)
            
            if not chunks_with_metadata:
                return DocumentResponse(
                    status="error",
                    message="Failed to create text chunks",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"✂️ Created {len(chunks_with_metadata)} enhanced chunks")
            
            # Store chunks with enhanced metadata
            for chunk_text, metadata in chunks_with_metadata:
                try:
                    embedding = self.base_system.get_embedding(chunk_text)
                    chunk_id = f"{filename}_{metadata.chunk_index}_{metadata.chunk_hash}"
                    
                    self.base_system.collection.add(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk_text],
                        metadatas=[self.processor.create_searchable_metadata_dict(metadata)]
                    )
                except Exception as e:
                    logger.error(f"Failed to process chunk {metadata.chunk_index}: {e}")
                    continue
            
            # Upload to S3 if configured
            if self.base_system.s3_client:
                try:
                    self.base_system.s3_client.put_object(
                        Bucket=config.S3_BUCKET,
                        Key=f"documents/{filename}",
                        Body=file_content,
                        Metadata={'original_name': filename}
                    )
                    logger.info(f"☁️ Uploaded to S3: {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ S3 upload failed: {e}")
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Enhanced processing completed for {filename} in {processing_time:.2f}s")
            
            return DocumentResponse(
                status="success",
                message=f"Successfully processed {len(chunks_with_metadata)} chunks with enhanced metadata",
                chunks_created=len(chunks_with_metadata),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced document processing failed: {e}")
            return DocumentResponse(
                status="error",
                message=f"Processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def search_and_answer_enhanced(self, query: str, top_k: int = 3) -> ChatResponse:
        """Enhanced search with better source attribution"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing enhanced query: {query}")
            
            # Generate query embedding
            query_embedding = self.base_system.get_embedding(query)
            
            # Search for relevant chunks
            results = self.base_system.collection.query(
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
                # Create enhanced context with location info
                location_ref = metadata.get('location_reference', 'Unknown location')
                summary = metadata.get('chunk_summary', 'No summary available')
                
                enhanced_chunk = f"[Source: {location_ref}]\n{chunk}\n[Summary: {summary}]\n"
                context_chunks.append(enhanced_chunk)
                
                # Create detailed source info
                source_detail = f"{metadata['filename']} ({location_ref})"
                source_info.append(source_detail)
            
            context = "\n---\n".join(context_chunks)
            
            logger.info(f"📚 Found {len(context_chunks)} relevant chunks with enhanced metadata")
            
            # Generate answer with location awareness
            response = self.base_system.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
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
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            logger.info(f"💬 Generated enhanced answer in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=source_info,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Enhanced search and answer failed: {e}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
