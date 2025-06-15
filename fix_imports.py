#!/usr/bin/env python3
"""
Script to fix all imports after directory reorganization
"""

import os
import re
from pathlib import Path


def update_imports_in_file(file_path: Path, import_mapping: dict):
    """Update imports in a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports
        for old_import, new_import in import_mapping.items():
            # Handle different import patterns
            patterns = [
                f"from {old_import} import",
                f"import {old_import}",
            ]
            
            for pattern in patterns:
                if pattern in content:
                    if "from" in pattern:
                        content = content.replace(f"from {old_import} import", f"from {new_import} import")
                    else:
                        content = content.replace(f"import {old_import}", f"import {new_import}")
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def main():
    """Main function to update all imports"""
    
    # Define import mapping from old to new
    import_mapping = {
        # Core modules
        "config": "core.config",
        "models": "core.models", 
        "clients": "core.clients",
        "utils": "core.utils",
        
        # Processing modules
        "document_processor": "processing.document_processor",
        "hierarchical_processor": "processing.hierarchical_processor", 
        "paragraph_processor": "processing.paragraph_processor",
        "text_processing": "processing.text_processing",
        
        # Search modules
        "search_engine": "search.search_engine",
        "rag_system": "search.rag_system",
    }
    
    # Find all Python files in src directory
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    updated_files = 0
    total_files = len(python_files)
    
    print(f"Updating imports in {total_files} Python files...")
    
    for file_path in python_files:
        if update_imports_in_file(file_path, import_mapping):
            updated_files += 1
    
    print(f"\nCompleted: Updated {updated_files} out of {total_files} files")


if __name__ == "__main__":
    main()