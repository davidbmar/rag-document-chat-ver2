#!/usr/bin/env python3
"""
RAG Document Chat System
A complete retrieval augmented generation system for document Q&A
"""

import os
import asyncio
import sys
import time
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Core dependencies
import boto3
import chromadb
from openai import OpenAI
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2
import io

import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    """System configuration from environment variables"""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8002"))
    
    @property
    def s3_enabled(self) -> bool:
        return bool(self.S3_BUCKET and self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)
    
    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith("sk-"))

config = Config()

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    top_k: int = 3

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    processing_time: float

class DocumentResponse(BaseModel):
    status: str
    message: str
    chunks_created: int = 0
    processing_time: float = 0.0


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
        # First, split into paragraphs
        paragraphs = self._split_by_paragraphs(text)
        
        # Then process each paragraph into sentence-aware chunks
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
            if para and len(para) > 20:  # Ignore very short paragraphs
                para = re.sub(r'\s+', ' ', para)  # Normalize whitespace
                cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with better accuracy"""
        sentences = nltk.sent_tokenize(text)
        
        # Post-process to handle abbreviations
        processed_sentences = []
        i = 0
        
        while i < len(sentences):
            current_sentence = sentences[i]
            
            # Check if current sentence ends with abbreviation
            if i < len(sentences) - 1:
                words = current_sentence.split()
                if words and any(current_sentence.rstrip().endswith(abbrev) for abbrev in self.abbreviations):
                    next_sentence = sentences[i + 1].strip()
                    if next_sentence and next_sentence[0].islower():
                        current_sentence += " " + next_sentence
                        i += 1  # Skip next sentence as we've merged it
            
            processed_sentences.append(current_sentence.strip())
            i += 1
        
        return [s for s in processed_sentences if s]
    
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
                
                # Handle overlap
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




class RAGSystem:
    """Main RAG system implementation"""
    
    def __init__(self):
        logger.info("Initializing RAG System...")
        
        # Initialize S3 client if enabled
        self.s3_client = None
        if config.s3_enabled:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=config.AWS_REGION
                )
                logger.info("✅ S3 client initialized")
            except Exception as e:
                logger.warning(f"⚠️ S3 initialization failed: {e}")
                self.s3_client = None
        else:
            logger.info("ℹ️ S3 not configured")
        
        # Initialize ChromaDB with retries
        self.chroma_client = None
        self.collection = None
        self._init_chromadb()
        
        # Initialize text splitter
        self.text_splitter = LogicalTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        # Initialize OpenAI client
        if config.openai_enabled:
            try:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                # Test connection
                self.openai_client.models.list()
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI initialization failed: {e}")
                raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        else:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")

    def _init_chromadb(self) -> None:
        """Initialize ChromaDB with connection retries"""
        for attempt in range(3):
            try:
                logger.info(f"🔄 Connecting to ChromaDB (attempt {attempt + 1}/3)...")
                
                # Simple HTTP client without any settings conflicts
                self.chroma_client = chromadb.HttpClient(
                    host=config.CHROMA_HOST, 
                    port=config.CHROMA_PORT
                )
                
                # Test connection with v2 API
                self.chroma_client.heartbeat()
                
                self.collection = self.chroma_client.get_or_create_collection(
                    name="documents",
                    metadata={"description": "RAG document collection"}
                )
                logger.info("✅ ChromaDB server connected")
                return
                
            except Exception as e:
                logger.warning(f"❌ ChromaDB connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)
        
        # Fallback to in-memory client
        logger.info("⚠️ Using in-memory ChromaDB (data will not persist)")
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection("documents")


    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from uploaded files"""
        file_ext = Path(filename).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text = ""
                for page_num, page in enumerate(reader.pages):
                    try:
                        text += page.extract_text() + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                return text.strip()
            
            elif file_ext == '.txt':
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    return file_content.decode('utf-8', errors='ignore')
            
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8191]  # OpenAI embedding limit
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def process_document(self, file_content: bytes, filename: str) -> DocumentResponse:
        """Process uploaded document: extract text, chunk, embed, and store"""
        start_time = time.time()
        
        try:
            logger.info(f"📄 Processing document: {filename}")
            
            # Extract text
            text = self.extract_text(file_content, filename)
            if not text.strip():
                return DocumentResponse(
                    status="error",
                    message="No text content found in document",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"📝 Extracted {len(text)} characters")
            
            # Upload to S3 if configured
            if self.s3_client:
                try:
                    self.s3_client.put_object(
                        Bucket=config.S3_BUCKET,
                        Key=f"documents/{filename}",
                        Body=file_content,
                        Metadata={'original_name': filename}
                    )
                    logger.info(f"☁️ Uploaded to S3: {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ S3 upload failed: {e}")
            
            # Chunk text
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                return DocumentResponse(
                    status="error",
                    message="Failed to create text chunks",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"✂️ Created {len(chunks)} chunks")
            
            # Generate embeddings and store
            for i, chunk in enumerate(chunks):
                try:
                    embedding = self.get_embedding(chunk)
                    chunk_id = f"{filename}_{i}"
                    
                    self.collection.add(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "filename": filename,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "chunk_size": len(chunk)
                        }]
                    )
                except Exception as e:
                    logger.error(f"Failed to process chunk {i}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Successfully processed {filename} in {processing_time:.2f}s")
            
            return DocumentResponse(
                status="success",
                message=f"Successfully processed {len(chunks)} chunks",
                chunks_created=len(chunks),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return DocumentResponse(
                status="error",
                message=f"Processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def search_and_answer(self, query: str, top_k: int = 3) -> ChatResponse:
        """Search documents and generate answer using RAG"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing query: {query}")
            
            # Generate query embedding
            query_embedding = self.get_embedding(query)
            
            # Search for relevant chunks
            results = self.collection.query(
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
            
            # Generate answer using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
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
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            logger.info(f"💬 Generated answer in {processing_time:.2f}s")
            
            return ChatResponse(
                answer=answer,
                sources=list(set(sources)),  # Remove duplicates
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Search and answer failed: {e}")
            return ChatResponse(
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=time.time() - start_time
            )
    
    def get_system_status(self) -> Dict:
        """Get system component status"""
        status = {
            "chromadb": "disconnected",
            "openai": "disconnected",
            "s3": "disabled"
        }
        
        # Check ChromaDB
        try:
            if hasattr(self.chroma_client, 'heartbeat'):
                self.chroma_client.heartbeat()
                status["chromadb"] = "connected"
            else:
                status["chromadb"] = "in-memory"
        except:
            status["chromadb"] = "disconnected"
        
        # Check OpenAI
        if config.openai_enabled:
            try:
                self.openai_client.models.list()
                status["openai"] = "connected"
            except:
                status["openai"] = "error"
        
        # Check S3
        if config.s3_enabled and self.s3_client:
            try:
                self.s3_client.head_bucket(Bucket=config.S3_BUCKET)
                status["s3"] = "connected"
            except:
                status["s3"] = "error"
        
        return status

# Initialize RAG system
rag_system = RAGSystem()

# FastAPI Application
app = FastAPI(
    title="RAG Document Chat API",
    description="Retrieval Augmented Generation system for document Q&A",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RAG Document Chat API is running!",
        "status": rag_system.get_system_status()
    }

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Process document
        result = await rag_system.process_document(content, file.filename)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Ask questions about uploaded documents"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = rag_system.search_and_answer(request.query, request.top_k)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get system status"""
    return rag_system.get_system_status()

# Streamlit Interface
def create_streamlit_app():
    """Create Streamlit web interface"""
    
    st.set_page_config(
        page_title="RAG Document Chat",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 RAG Document Chat System")
    st.markdown("Upload documents and chat with them using AI!")
    
    # Sidebar for system status and file upload
    with st.sidebar:
        st.header("📊 System Status")
        
        status = rag_system.get_system_status()
        
        # Status indicators
        chromadb_status = "🟢" if status["chromadb"] == "connected" else "🟡" if status["chromadb"] == "in-memory" else "🔴"
        openai_status = "🟢" if status["openai"] == "connected" else "🔴"
        s3_status = "🟢" if status["s3"] == "connected" else "🟡" if status["s3"] == "disabled" else "🔴"
        
        st.markdown(f"**ChromaDB:** {chromadb_status} {status['chromadb']}")
        st.markdown(f"**OpenAI:** {openai_status} {status['openai']}")
        st.markdown(f"**S3:** {s3_status} {status['s3']}")
        
        st.divider()
        
        # File upload section
        st.header("📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'txt'],
            help="Upload PDF or TXT files to add to your knowledge base"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Process Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    try:
                        # Process the document
                        result = asyncio.run(rag_system.process_document(
                            uploaded_file.read(), uploaded_file.name
                        ))
                        
                        if result.status == "success":
                            st.success(f"✅ {result.message}")
                            st.info(f"⏱️ Processed in {result.processing_time:.2f}s")
                        else:
                            st.error(f"❌ {result.message}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # Main chat interface
    st.header("💬 Chat with Your Documents")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources for assistant messages
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Sources", expanded=False):
                    for source in message["sources"]:
                        st.text(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = rag_system.search_and_answer(prompt)
                    
                    # Display answer
                    st.markdown(response.answer)
                    
                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "sources": response.sources
                    })
                    
                    # Show sources
                    if response.sources:
                        with st.expander("📚 Sources", expanded=False):
                            for source in response.sources:
                                st.text(f"• {source}")
                    
                    # Show processing time
                    st.caption(f"⏱️ Response generated in {response.processing_time:.2f}s")
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })

def main():
    """Main application entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "streamlit":
            # Run Streamlit interface
            create_streamlit_app()
        elif sys.argv[1] == "api":
            # Run FastAPI server
            import uvicorn
            logger.info("🚀 Starting FastAPI server...")
            uvicorn.run(app, host="0.0.0.0", port=8001)
        else:
            print("Usage: python app.py [streamlit|api]")
            print("  streamlit - Run web interface (default)")
            print("  api      - Run API server")
            sys.exit(1)
    else:
        # Default to Streamlit
        create_streamlit_app()

if __name__ == "__main__":
    main()
