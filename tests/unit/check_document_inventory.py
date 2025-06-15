#!/usr/bin/env python3
"""
Check the actual document inventory by connecting to ChromaDB directly
"""

import chromadb
import json
from typing import Dict, Any

def get_document_inventory():
    """Get comprehensive document inventory from ChromaDB"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host="localhost", port=8002)
        
        # Get all collections
        collections = client.list_collections()
        
        inventory = {
            "total_collections": len(collections),
            "collections": {},
            "total_documents": 0,
            "documents_by_filename": {},
            "summary": {}
        }
        
        for collection in collections:
            collection_name = collection.name
            
            # Get collection data
            collection_obj = client.get_collection(collection_name)
            data = collection_obj.get()
            
            item_count = len(data.get('ids', []))
            inventory["total_documents"] += item_count
            
            # Analyze documents
            filenames = set()
            sample_docs = []
            sample_metadata = []
            
            if data.get('metadatas'):
                for i, metadata in enumerate(data['metadatas']):
                    if isinstance(metadata, dict):
                        filename = metadata.get('filename', 'unknown')
                        filenames.add(filename)
                        
                        # Track by filename
                        if filename not in inventory["documents_by_filename"]:
                            inventory["documents_by_filename"][filename] = {
                                "collections": {},
                                "total_items": 0
                            }
                        
                        if collection_name not in inventory["documents_by_filename"][filename]["collections"]:
                            inventory["documents_by_filename"][filename]["collections"][collection_name] = 0
                        
                        inventory["documents_by_filename"][filename]["collections"][collection_name] += 1
                        inventory["documents_by_filename"][filename]["total_items"] += 1
                    
                    # Collect samples
                    if i < 3:
                        sample_metadata.append(metadata)
            
            if data.get('documents'):
                for i, doc in enumerate(data['documents']):
                    if i < 3:
                        sample_docs.append(doc[:100] + "..." if len(doc) > 100 else doc)
            
            inventory["collections"][collection_name] = {
                "item_count": item_count,
                "filenames": list(filenames),
                "sample_documents": sample_docs,
                "sample_metadata": sample_metadata,
                "description": collection.metadata.get('description', 'No description') if collection.metadata else 'No description'
            }
        
        # Create summary
        inventory["summary"] = {
            "unique_files": len(inventory["documents_by_filename"]),
            "files_list": list(inventory["documents_by_filename"].keys()),
            "collections_with_data": [name for name, data in inventory["collections"].items() if data["item_count"] > 0],
            "has_documents": inventory["total_documents"] > 0
        }
        
        return inventory
        
    except Exception as e:
        return {"error": str(e)}

def main():
    print("📊 Document Inventory Report")
    print("=" * 50)
    
    inventory = get_document_inventory()
    
    if "error" in inventory:
        print(f"❌ Error: {inventory['error']}")
        return
    
    # Print summary
    print(f"🗄️  Total Collections: {inventory['total_collections']}")
    print(f"📄 Total Documents: {inventory['total_documents']}")
    print(f"📁 Unique Files: {inventory['summary']['unique_files']}")
    print()
    
    # Print files
    if inventory["summary"]["files_list"]:
        print("📁 Files Found:")
        for filename in inventory["summary"]["files_list"]:
            file_data = inventory["documents_by_filename"][filename]
            print(f"  • {filename} ({file_data['total_items']} items)")
            for collection, count in file_data["collections"].items():
                print(f"    └─ {collection}: {count} items")
        print()
    
    # Print collections
    print("🗄️  Collections Breakdown:")
    for collection_name, collection_data in inventory["collections"].items():
        print(f"  📦 {collection_name}:")
        print(f"     Items: {collection_data['item_count']}")
        print(f"     Description: {collection_data['description']}")
        print(f"     Files: {', '.join(collection_data['filenames']) if collection_data['filenames'] else 'None'}")
        
        if collection_data["sample_metadata"]:
            print(f"     Sample metadata: {collection_data['sample_metadata'][0]}")
        
        if collection_data["sample_documents"]:
            print(f"     Sample document: {collection_data['sample_documents'][0]}")
        print()
    
    # Save to file
    with open('/home/ubuntu/src/rag-document-chat-ver2/document_inventory.json', 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print("💾 Full inventory saved to document_inventory.json")

if __name__ == "__main__":
    main()