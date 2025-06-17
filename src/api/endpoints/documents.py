"""
Document processing and management API endpoints
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from src.core.models import DocumentResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process/upload", response_model=DocumentResponse)
async def process_upload(file: UploadFile = File(...), force: bool = False):
    """Upload and process document with basic chunking and duplicate detection"""
    from src.api.app import rag_system
    
    try:
        # Input validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.filename.lower().endswith(('.pdf', '.txt', '.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only PDF, TXT, and image files are supported")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Check for existing document
        if not force:
            existing_doc = await _check_document_exists(rag_system, file.filename)
            if existing_doc:
                logger.info(f"📄 Document already exists: {file.filename}")
                return DocumentResponse(
                    status="already_exists",
                    message=f"Document '{file.filename}' already exists with {existing_doc['chunk_count']} chunks. Use force=true to overwrite.",
                    chunks_created=existing_doc['chunk_count'],
                    processing_time=0.0
                )
        
        # Process the document
        logger.info(f"📄 Processing document: {file.filename}")
        result = await rag_system.process_document(content, file.filename)
        
        # Return success response
        return DocumentResponse(
            status="success",
            message=f"Successfully processed '{file.filename}'",
            chunks_created=len(result.chunks) if hasattr(result, 'chunks') else result.chunks_created,
            processing_time=result.processing_time if hasattr(result, 'processing_time') else 0.0
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Process upload error for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process document '{file.filename}': {str(e)}"
        )


async def _check_document_exists(rag_system, filename: str) -> dict:
    """Check if a document already exists in the system"""
    try:
        # Check original_texts collection for the document
        original_collection = rag_system.clients.chromadb.get_or_create_collection("original_texts")
        results = original_collection.get(
            where={"filename": filename},
            limit=1
        )
        
        if results and results.get('ids'):
            # Document exists, count total chunks across all collections
            total_chunks = 0
            collections = rag_system.clients.chromadb.client.list_collections()
            
            for collection_info in collections:
                try:
                    collection = rag_system.clients.chromadb.get_or_create_collection(collection_info.name)
                    collection_results = collection.get(
                        where={"filename": filename}
                    )
                    if collection_results and collection_results.get('ids'):
                        total_chunks += len(collection_results['ids'])
                except Exception as e:
                    logger.warning(f"Error checking collection {collection_info.name}: {e}")
            
            return {
                "exists": True,
                "chunk_count": total_chunks,
                "filename": filename
            }
        
        return None
        
    except Exception as e:
        logger.warning(f"Error checking document existence for {filename}: {e}")
        return None


@router.post("/process/{filename}/summaries", response_model=DocumentResponse)
async def process_summaries(filename: str):
    """Generate smart summaries for a processed document"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"🧠 Processing summaries for: {filename}")
        result = await rag_system.process_document_hierarchically(filename)
        return DocumentResponse(
            status=result.status,
            message=result.message,
            chunks_created=result.summaries_created,
            processing_time=result.total_processing_time
        )
    except Exception as e:
        logger.error(f"Process summaries error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/{filename}/paragraphs", response_model=DocumentResponse)
async def process_paragraphs(filename: str):
    """Generate paragraph summaries for a processed document"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"📝 Processing paragraphs for: {filename}")
        result = await rag_system.process_document_paragraphs(filename)
        return DocumentResponse(
            status=result.status,
            message=result.message,
            chunks_created=result.paragraphs_processed,
            processing_time=result.total_processing_time
        )
    except Exception as e:
        logger.error(f"Process paragraphs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    """List all processed documents"""
    from src.api.app import rag_system
    
    try:
        # Get document inventory from ChromaDB
        status_data = {
            'documents': {},
            'total_items': 0,
            'collections': []
        }
        
        # Check all collections
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                items = collection.get()
                
                count = len(items.get('ids', []))
                status_data['total_items'] += count
                status_data['collections'].append({
                    'name': collection_name,
                    'count': count
                })
                
                # Track documents
                if 'metadatas' in items and items['metadatas']:
                    for metadata in items['metadatas']:
                        if isinstance(metadata, dict) and 'filename' in metadata:
                            filename = metadata['filename']
                            if filename not in status_data['documents']:
                                status_data['documents'][filename] = {
                                    'collections': {},
                                    'total_chunks': 0
                                }
                            
                            if collection_name not in status_data['documents'][filename]['collections']:
                                status_data['documents'][filename]['collections'][collection_name] = 0
                            
                            status_data['documents'][filename]['collections'][collection_name] += 1
                            status_data['documents'][filename]['total_chunks'] += 1
                            
            except Exception as e:
                logger.warning(f"Error accessing collection {collection_name}: {e}")
        
        return status_data
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def clear_all_documents():
    """Clear all documents and reset system"""
    from src.api.app import rag_system
    
    try:
        logger.info("🧹 API Clear all documents request")
        
        # Get all collections
        collections = rag_system.clients.chromadb.client.list_collections()
        cleared_collections = []
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                
                # Get all items to count them
                items = collection.get()
                item_count = len(items.get('ids', []))
                
                if item_count > 0:
                    # Clear the collection
                    collection.delete(ids=items['ids'])
                    cleared_collections.append({
                        'name': collection_name,
                        'items_deleted': item_count
                    })
                    
            except Exception as e:
                logger.warning(f"Error clearing collection {collection_name}: {e}")
        
        return {
            'status': 'success',
            'message': f'Cleared {len(cleared_collections)} collections',
            'cleared_collections': cleared_collections
        }
        
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))