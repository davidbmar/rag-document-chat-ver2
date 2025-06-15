"""
Search and question-answering API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException

from src.core.models import SearchRequest, SearchResponse, AskRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents with filtering and result persistence"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"🔍 API Search request: {request.query}")
        result = rag_system.search_engine.search_documents(request)
        return result
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: AskRequest):
    """Ask questions with context filtering and search result reuse"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"💬 API Ask request: {request.question}")
        result = rag_system.search_engine.ask_with_context(request)
        return result
    except Exception as e:
        logger.error(f"Ask API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))