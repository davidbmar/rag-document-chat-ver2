#!/usr/bin/env python3
"""
Quick status check script to see what documents are indexed
"""

import requests
import json
from rag_system import RAGSystem

def check_current_status():
    """Check the current status of indexed documents"""
    print("🔍 DOCUMENT STATUS CHECK")
    print("=" * 50)
    
    try:
        # Initialize RAG system
        rag = RAGSystem()
        
        # Get all collections
        collections = rag.clients.chromadb.client.list_collections()
        
        total_items = 0
        documents_by_file = {}
        
        print(f"📊 Found {len(collections)} collections")
        print()
        
        for collection_info in collections:
            collection_name = collection_info.name
            try:
                collection = rag.clients.chromadb.get_or_create_collection(collection_name)
                items = collection.get()
                count = len(items.get('ids', []))
                total_items += count
                
                print(f"🗄️ {collection_name}: {count} items")
                
                # Show sample files
                if items.get('metadatas'):
                    filenames = set()
                    for meta in items['metadatas']:
                        if isinstance(meta, dict) and 'filename' in meta:
                            filename = meta['filename']
                            filenames.add(filename)
                            
                            # Track by document
                            if filename not in documents_by_file:
                                documents_by_file[filename] = {}
                            documents_by_file[filename][collection_name] = documents_by_file[filename].get(collection_name, 0) + 1
                    
                    if filenames:
                        print(f"   📄 Files: {', '.join(sorted(filenames))}")
                    
                    # Show sample metadata
                    if count > 0:
                        sample = items['metadatas'][0]
                        if 'chunk_index' in sample:
                            print(f"   📝 Sample: chunk {sample.get('chunk_index', '?')} of {sample.get('total_chunks', '?')}")
                        elif 'group_id' in sample:
                            print(f"   🧠 Sample: {sample.get('group_id', '?')} (compression: {sample.get('compression_ratio', '?')})")
                        elif 'paragraph_index' in sample:
                            print(f"   📄 Sample: paragraph {sample.get('paragraph_index', '?')} of {sample.get('total_paragraphs', '?')}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error accessing {collection_name}: {e}")
                print()
        
        print("=" * 50)
        print(f"📊 SUMMARY:")
        print(f"   Total items: {total_items}")
        print(f"   Unique documents: {len(documents_by_file)}")
        
        if documents_by_file:
            print(f"\n📄 DOCUMENTS:")
            for filename, collections_data in documents_by_file.items():
                total_for_file = sum(collections_data.values())
                print(f"   {filename}: {total_for_file} items")
                for coll_name, count in collections_data.items():
                    print(f"     └─ {coll_name}: {count}")
        
        # Check S3 status
        try:
            from config import config
            if hasattr(rag.clients, 's3') and rag.clients.s3 and config.s3_bucket:
                s3_response = rag.clients.s3.list_objects_v2(Bucket=config.s3_bucket)
                if 'Contents' in s3_response:
                    s3_files = [obj['Key'] for obj in s3_response['Contents']]
                    print(f"\n☁️ S3 STORAGE: {len(s3_files)} files")
                    for filename in sorted(s3_files):
                        print(f"   {filename}")
                else:
                    print(f"\n☁️ S3 STORAGE: Empty")
            else:
                print(f"\n☁️ S3 STORAGE: Not configured")
        except Exception as e:
            print(f"\n☁️ S3 STORAGE: Error - {e}")
        
        return total_items > 0
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    check_current_status()