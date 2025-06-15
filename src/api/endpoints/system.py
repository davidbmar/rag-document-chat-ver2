"""
System-related API endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get system status"""
    from api.app import rag_system
    return rag_system.get_system_status()


@router.get("/api/collections")
async def get_collections_info():
    """Get detailed information about all ChromaDB collections"""
    from api.app import rag_system
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        collections_info = []
        
        collections = rag_system.clients.chromadb.client.list_collections()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag_system.clients.chromadb.get_or_create_collection(collection_name)
                items = collection.get()
                
                # Extract unique filenames
                filenames = set()
                if 'metadatas' in items and items['metadatas']:
                    for metadata in items['metadatas']:
                        if isinstance(metadata, dict) and 'filename' in metadata:
                            filenames.add(metadata['filename'])
                
                collections_info.append({
                    'name': collection_name,
                    'item_count': len(items.get('ids', [])),
                    'unique_documents': list(filenames),
                    'sample_ids': items.get('ids', [])[:3]
                })
                
            except Exception as e:
                collections_info.append({
                    'name': collection_name,
                    'error': str(e)
                })
        
        return {
            'collections': collections_info,
            'total_collections': len(collections_info)
        }
        
    except Exception as e:
        logger.error(f"Collections info error: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))