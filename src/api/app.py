"""
FastAPI Application Setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.utils import setup_logging
from search.rag_system import RAGSystem

logger = setup_logging()

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

# Import and include routers
from api.endpoints import system, documents, search

app.include_router(system.router, tags=["system"])
app.include_router(documents.router, prefix="/api", tags=["documents"])  
app.include_router(search.router, prefix="/api", tags=["search"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RAG Document Chat API is running!",
        "status": rag_system.get_system_status()
    }