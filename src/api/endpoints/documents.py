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
    """List all processed documents with enhanced metadata"""
    from src.api.app import rag_system
    import os
    from datetime import datetime
    
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
                
                # Track documents with enhanced metadata
                if 'metadatas' in items and items['metadatas']:
                    for i, metadata in enumerate(items['metadatas']):
                        if isinstance(metadata, dict) and 'filename' in metadata:
                            filename = metadata['filename']
                            if filename not in status_data['documents']:
                                # Initialize document entry with enhanced metadata
                                status_data['documents'][filename] = {
                                    'collections': {},
                                    'total_chunks': 0,
                                    'status': 'processed',  # Default status
                                    'size': 'Unknown',
                                    'upload_date': 'Unknown',
                                    'processing_stages': [],
                                    'file_type': filename.split('.')[-1].upper() if '.' in filename else 'Unknown'
                                }
                                
                                # Try to get additional metadata from first occurrence
                                if collection_name == 'original_texts':
                                    # Get more detailed info from original_texts collection
                                    first_metadata = metadata
                                    if 'upload_date' in first_metadata:
                                        status_data['documents'][filename]['upload_date'] = first_metadata['upload_date']
                                    if 'file_size' in first_metadata:
                                        size_bytes = first_metadata['file_size']
                                        # Convert bytes to human readable
                                        if size_bytes < 1024:
                                            status_data['documents'][filename]['size'] = f"{size_bytes} B"
                                        elif size_bytes < 1024**2:
                                            status_data['documents'][filename]['size'] = f"{size_bytes/1024:.1f} KB"
                                        elif size_bytes < 1024**3:
                                            status_data['documents'][filename]['size'] = f"{size_bytes/(1024**2):.1f} MB"
                                        else:
                                            status_data['documents'][filename]['size'] = f"{size_bytes/(1024**3):.1f} GB"
                            
                            if collection_name not in status_data['documents'][filename]['collections']:
                                status_data['documents'][filename]['collections'][collection_name] = 0
                            
                            status_data['documents'][filename]['collections'][collection_name] += 1
                            status_data['documents'][filename]['total_chunks'] += 1
                            
                            # Track processing stages
                            if collection_name not in status_data['documents'][filename]['processing_stages']:
                                status_data['documents'][filename]['processing_stages'].append(collection_name)
                            
            except Exception as e:
                logger.warning(f"Error accessing collection {collection_name}: {e}")
        
        # Determine processing completeness for each document
        for filename, doc_info in status_data['documents'].items():
            stages = doc_info['processing_stages']
            if 'documents' in stages and 'logical_summaries' in stages and 'paragraph_summaries' in stages:
                doc_info['status'] = 'fully_processed'
            elif 'documents' in stages and ('logical_summaries' in stages or 'paragraph_summaries' in stages):
                doc_info['status'] = 'partially_processed'
            elif 'documents' in stages:
                doc_info['status'] = 'basic_processed'
            else:
                doc_info['status'] = 'incomplete'
        
        return status_data
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{filename}")
async def get_document_details(filename: str):
    """Get detailed information about a specific document"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"📄 Getting details for document: {filename}")
        
        document_details = {
            'filename': filename,
            'collections': {},
            'total_chunks': 0,
            'processing_stages': [],
            'chunks_by_collection': {},
            'sample_content': {},
            'status': 'not_found'
        }
        
        # Check all collections for this document
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                
                # Get items for this specific document
                items = collection.get(
                    where={"filename": filename},
                    limit=5  # Get first 5 chunks for preview
                )
                
                if items and items.get('ids'):
                    chunk_count = len(items['ids'])
                    document_details['collections'][collection_name] = chunk_count
                    document_details['total_chunks'] += chunk_count
                    document_details['processing_stages'].append(collection_name)
                    
                    # Store sample content from first chunk
                    if items.get('documents') and len(items['documents']) > 0:
                        sample_text = items['documents'][0]
                        # Truncate long content
                        if len(sample_text) > 300:
                            sample_text = sample_text[:300] + "..."
                        document_details['sample_content'][collection_name] = sample_text
                    
                    # Get detailed metadata from first chunk
                    if items.get('metadatas') and len(items['metadatas']) > 0:
                        metadata = items['metadatas'][0]
                        if collection_name == 'original_texts' and isinstance(metadata, dict):
                            document_details['metadata'] = metadata
                            
            except Exception as e:
                logger.warning(f"Error getting details from collection {collection_name}: {e}")
        
        if document_details['total_chunks'] > 0:
            document_details['status'] = 'found'
            
            # Determine processing completeness
            stages = document_details['processing_stages']
            if 'documents' in stages and 'logical_summaries' in stages and 'paragraph_summaries' in stages:
                document_details['processing_status'] = 'fully_processed'
            elif 'documents' in stages and ('logical_summaries' in stages or 'paragraph_summaries' in stages):
                document_details['processing_status'] = 'partially_processed'
            elif 'documents' in stages:
                document_details['processing_status'] = 'basic_processed'
            else:
                document_details['processing_status'] = 'incomplete'
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{filename}' not found in any collection"
            )
        
        return document_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document details error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document from all collections"""
    from src.api.app import rag_system
    
    try:
        logger.info(f"🗑️ Deleting document: {filename}")
        
        # Track deletion results
        deletion_results = {
            'filename': filename,
            'collections_affected': [],
            'total_chunks_deleted': 0,
            'status': 'success'
        }
        
        # Get all collections
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                
                # Find items for this filename
                items = collection.get(
                    where={"filename": filename}
                )
                
                if items and items.get('ids'):
                    chunk_count = len(items['ids'])
                    # Delete all chunks for this document
                    collection.delete(ids=items['ids'])
                    
                    deletion_results['collections_affected'].append({
                        'collection': collection_name,
                        'chunks_deleted': chunk_count
                    })
                    deletion_results['total_chunks_deleted'] += chunk_count
                    
                    logger.info(f"  📦 Deleted {chunk_count} chunks from {collection_name}")
                    
            except Exception as e:
                logger.warning(f"Error deleting from collection {collection_name}: {e}")
                deletion_results['status'] = 'partial_success'
        
        if deletion_results['total_chunks_deleted'] == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{filename}' not found in any collection"
            )
        
        logger.info(f"✅ Deleted {deletion_results['total_chunks_deleted']} chunks from {len(deletion_results['collections_affected'])} collections")
        
        return {
            'status': deletion_results['status'],
            'message': f"Successfully deleted '{filename}' ({deletion_results['total_chunks_deleted']} chunks from {len(deletion_results['collections_affected'])} collections)",
            'deletion_results': deletion_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error for {filename}: {e}")
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