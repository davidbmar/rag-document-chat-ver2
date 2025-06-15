#!/usr/bin/env python3
"""
Text processing utilities for RAG Document Chat System
"""

import re
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
try:
    import nltk
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    nltk = None

from core.models import ChunkMetadata

logger = logging.getLogger(__name__)


class LogicalTextSplitter:
    """Enhanced text splitter that respects sentence and paragraph boundaries"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Common abbreviations that shouldn't end sentences
        self.abbreviations = {
            'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'vs.', 'etc.', 
            'i.e.', 'e.g.', 'cf.', 'al.', 'Inc.', 'Ltd.', 'Corp.',
            'St.', 'Ave.', 'Blvd.', 'Dept.', 'Fig.', 'Vol.', 'No.'
        }
    
    def split_text(self, text: str) -> List[str]:
        """Split text into logical chunks that respect sentence boundaries"""
        paragraphs = self._split_by_paragraphs(text)
        
        all_chunks = []
        for paragraph in paragraphs:
            paragraph_chunks = self._chunk_paragraph(paragraph)
            all_chunks.extend(paragraph_chunks)
        
        return all_chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:
                para = re.sub(r'\s+', ' ', para)
                cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with better accuracy"""
        if NLTK_AVAILABLE:
            sentences = nltk.sent_tokenize(text)
        else:
            # Simple fallback sentence splitting
            sentences = self._simple_sentence_split(text)
        
        processed_sentences = []
        i = 0
        
        while i < len(sentences):
            current_sentence = sentences[i]
            
            if i < len(sentences) - 1:
                words = current_sentence.split()
                if words and any(current_sentence.rstrip().endswith(abbrev) for abbrev in self.abbreviations):
                    next_sentence = sentences[i + 1].strip()
                    if next_sentence and next_sentence[0].islower():
                        current_sentence += " " + next_sentence
                        i += 1
            
            processed_sentences.append(current_sentence.strip())
            i += 1
        
        return [s for s in processed_sentences if s]
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitting without NLTK"""
        # Split on common sentence endings
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in '.!?':
                # Check if this looks like a sentence ending
                next_char_pos = text.find(char) + 1
                if next_char_pos < len(text):
                    next_char = text[next_char_pos:next_char_pos+1]
                    if next_char.isspace() or next_char.isupper():
                        sentences.append(current.strip())
                        current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return [s for s in sentences if len(s) > 10]
    
    def _chunk_paragraph(self, paragraph: str) -> List[str]:
        """Split a paragraph into logical chunks respecting sentence boundaries"""
        if len(paragraph) <= self.chunk_size:
            return [paragraph]
        
        sentences = self._split_into_sentences(paragraph)
        chunks = []
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                if self.chunk_overlap > 0 and current_sentences:
                    overlap_text = ""
                    overlap_chars = 0
                    
                    for prev_sentence in reversed(current_sentences):
                        if overlap_chars + len(prev_sentence) <= self.chunk_overlap:
                            overlap_text = prev_sentence + " " + overlap_text if overlap_text else prev_sentence
                            overlap_chars += len(prev_sentence)
                        else:
                            break
                    
                    current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                    current_sentences = [sentence] if not overlap_text else overlap_text.split() + [sentence]
                else:
                    current_chunk = sentence
                    current_sentences = [sentence]
            else:
                current_chunk = potential_chunk
                current_sentences.append(sentence)
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class DocumentMetadataExtractor:
    """Extract metadata from document chunks"""
    
    def extract_page_numbers(self, text: str) -> Dict[int, int]:
        """Extract page numbers and their positions in text"""
        page_positions = {}
        page_patterns = [
            r'Page\s+(\d+)',
            r'page\s+(\d+)',
            r'\[Page\s+(\d+)\]',
            r'(?:^|\n)\s*(\d+)\s*(?:\n|$)'
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
        
        patterns = [
            r'^#{1,6}\s+(.+)$',
            r'^([A-Z][A-Z\s]{2,})$',
            r'^\d+\.\s+(.+)$',
            r'^Chapter\s+\d+:?\s*(.*)$',
            r'^\*\*(.+)\*\*$'
        ]
        
        lines = text.split('\n')
        char_position = 0
        
        for line in lines:
            line_stripped = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 3:
                        section_positions[char_position] = title
                    break
            char_position += len(line) + 1
        
        return section_positions
    
    def generate_chunk_summary(self, chunk_text: str, max_length: int = 120) -> str:
        """Generate a concise summary of the chunk content"""
        clean_text = re.sub(r'\s+', ' ', chunk_text.strip())
        sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 10]
        
        if sentences:
            summary = sentences[0]
            if len(summary) < 50 and len(sentences) > 1:
                summary += ". " + sentences[1]
        else:
            summary = clean_text[:max_length]
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def extract_key_terms(self, chunk_text: str, max_terms: int = 5) -> List[str]:
        """Extract key terms from chunk text"""
        text = re.sub(r'[^\w\s]', ' ', chunk_text)
        words = text.split()
        
        capitalized = [w for w in words if w[0].isupper() and len(w) > 2]
        long_words = [w.lower() for w in words if len(w) > 6]
        
        key_terms = list(set(capitalized + long_words))
        term_freq = {term: chunk_text.lower().count(term.lower()) for term in key_terms}
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [term for term, freq in sorted_terms[:max_terms]]
    
    def determine_content_type(self, chunk_text: str) -> str:
        """Determine the type of content in the chunk"""
        text_lower = chunk_text.lower()
        
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
    
    def get_position_metadata(self, text: str, position: int, 
                            page_positions: Dict[int, int], 
                            section_positions: Dict[int, str]) -> Tuple[Optional[int], Optional[str], int]:
        """Get page number, section title, and paragraph number for position"""
        
        # Page number
        page_number = None
        if page_positions:
            relevant_pages = [(pos, page) for pos, page in page_positions.items() if pos <= position]
            if relevant_pages:
                page_number = max(relevant_pages, key=lambda x: x[0])[1]
        
        # Section title
        section_title = None
        if section_positions:
            relevant_sections = [(pos, title) for pos, title in section_positions.items() if pos <= position]
            if relevant_sections:
                section_title = max(relevant_sections, key=lambda x: x[0])[1]
        
        # Paragraph number
        text_before = text[:position]
        paragraph_number = text_before.count('\n\n') + 1
        
        return page_number, section_title, paragraph_number


class EnhancedDocumentProcessor:
    """Enhanced document processor with comprehensive metadata"""
    
    def __init__(self):
        self.text_splitter = LogicalTextSplitter()
        self.metadata_extractor = DocumentMetadataExtractor()
    
    def process_document_with_metadata(self, text: str, filename: str) -> List[Tuple[str, ChunkMetadata]]:
        """Process document and create enhanced metadata for each chunk"""
        
        page_positions = self.metadata_extractor.extract_page_numbers(text)
        section_positions = self.metadata_extractor.extract_section_titles(text)
        
        chunks = []
        current_position = 0
        
        text_chunks = self.text_splitter.split_text(text)
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_start = text.find(chunk_text, current_position)
            if chunk_start == -1:
                chunk_start = current_position
            
            chunk_end = chunk_start + len(chunk_text)
            current_position = chunk_end
            
            page_number, section_title, paragraph_number = self.metadata_extractor.get_position_metadata(
                text, chunk_start, page_positions, section_positions
            )
            
            metadata = ChunkMetadata(
                filename=filename,
                chunk_index=i,
                total_chunks=len(text_chunks),
                chunk_size=len(chunk_text),
                chunk_summary=self.metadata_extractor.generate_chunk_summary(chunk_text),
                page_number=page_number,
                section_title=section_title,
                start_char=chunk_start,
                end_char=chunk_end,
                paragraph_number=paragraph_number,
                content_type=self.metadata_extractor.determine_content_type(chunk_text),
                key_terms=self.metadata_extractor.extract_key_terms(chunk_text),
                chunk_hash=hashlib.md5(chunk_text.encode()).hexdigest()[:12]
            )
            
            chunks.append((chunk_text, metadata))
        
        return chunks
    
    def create_metadata_dict(self, metadata: ChunkMetadata) -> Dict:
        """Convert metadata to dictionary for storage"""
        return {
            "filename": metadata.filename,
            "chunk_index": metadata.chunk_index,
            "total_chunks": metadata.total_chunks,
            "chunk_size": metadata.chunk_size,
            "chunk_summary": metadata.chunk_summary or "",
            "page_number": metadata.page_number or 0,
            "section_title": metadata.section_title or "Unknown Section",
            "start_char": metadata.start_char,
            "end_char": metadata.end_char,
            "paragraph_number": metadata.paragraph_number,
            "content_type": metadata.content_type,
            "key_terms": ", ".join(metadata.key_terms) if metadata.key_terms else "",
            "chunk_hash": metadata.chunk_hash,
            "location_reference": f"Page {metadata.page_number or 'N/A'}, Section: {metadata.section_title or 'Unknown'}, Paragraph {metadata.paragraph_number}"
        }