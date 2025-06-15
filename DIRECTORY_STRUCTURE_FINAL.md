# RAG Document Chat - Directory Structure

## Overview
This document describes the organized directory structure of the RAG Document Chat system, which follows Python packaging best practices with clear separation of concerns.

## Directory Structure

```
rag-document-chat-ver2/
├── README.md                    # Project overview and setup instructions
├── requirements.txt             # Python dependencies
├── .env                        # Environment configuration
├── .gitignore                  # Git ignore patterns
├── CLAUDE.md                   # Development instructions
│
├── src/                        # Main source code directory
│   ├── __init__.py            # Package marker
│   ├── main.py                # Main entry point for the application
│   ├── cli.py                 # Command-line interface
│   │
│   ├── core/                  # Core system components
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── models.py          # Pydantic data models
│   │   ├── clients.py         # External service clients (OpenAI, ChromaDB)
│   │   └── utils.py           # Common utilities
│   │
│   ├── processing/            # Document processing modules
│   │   ├── __init__.py
│   │   ├── document_processor.py      # Basic document processing
│   │   ├── hierarchical_processor.py  # Smart summary generation
│   │   ├── paragraph_processor.py     # Paragraph-level processing
│   │   └── text_processing.py         # Text utilities
│   │
│   ├── search/                # Search and RAG functionality
│   │   ├── __init__.py
│   │   ├── search_engine.py   # Core search and QA engine
│   │   └── rag_system.py      # Main RAG system orchestrator
│   │
│   ├── api/                   # REST API components
│   │   ├── __init__.py
│   │   ├── app.py             # FastAPI application
│   │   └── endpoints/         # API endpoint modules
│   │       ├── __init__.py
│   │       ├── documents.py   # Document processing endpoints
│   │       ├── search.py      # Search and ask endpoints
│   │       └── system.py      # System status endpoints
│   │
│   └── ui/                    # User interface components
│       ├── __init__.py
│       └── streamlit_app.py   # Streamlit web interface
│
├── tests/                     # Test files (moved from root)
│   ├── __init__.py
│   ├── test_*.py             # Individual test files
│   └── integration/          # Integration tests
│
├── scripts/                  # Utility scripts
│   ├── fix_imports.py        # Import path fixing script
│   └── setup/               # Setup and deployment scripts
│
└── docs/                     # Documentation
    ├── DIRECTORY_STRUCTURE.md # This file
    └── API.md               # API documentation
```

## Key Components

### Core Modules (`src/core/`)
- **config.py**: Centralized configuration management using environment variables
- **models.py**: Pydantic data models for request/response validation
- **clients.py**: Wrapper classes for external services (OpenAI, ChromaDB)
- **utils.py**: Common utilities (logging, NLTK setup, etc.)

### Processing Modules (`src/processing/`)
- **document_processor.py**: Basic document ingestion and chunking
- **hierarchical_processor.py**: Smart summary generation (10:1 compression)
- **paragraph_processor.py**: Paragraph-level summary processing (3:1 compression)
- **text_processing.py**: Text manipulation utilities

### Search Modules (`src/search/`)
- **search_engine.py**: Core search functionality with vector similarity and QA
- **rag_system.py**: Main orchestrator that coordinates all system components

### API Modules (`src/api/`)
- **app.py**: FastAPI application setup and configuration
- **endpoints/**: Organized API endpoints by functionality
  - **documents.py**: Document upload, processing, and management
  - **search.py**: Search and question-answering endpoints
  - **system.py**: System status and health checks

### UI Modules (`src/ui/`)
- **streamlit_app.py**: Web interface using Streamlit

## Entry Points

### Main Application
```bash
# Run the main application
python3 src/main.py
```

### API Server
```bash
# Run the FastAPI server
python3 src/api/app.py
```

### CLI Interface
```bash
# Use the command-line interface
python3 src/cli.py --help
```

### Streamlit UI
```bash
# Run the Streamlit web interface
streamlit run src/ui/streamlit_app.py
```

## Import Structure

The new structure uses proper Python package imports:

```python
# Core components
from core.config import config
from core.models import SearchRequest, ChatResponse
from core.clients import ClientManager

# Processing
from processing.document_processor import DocumentProcessor
from processing.hierarchical_processor import HierarchicalProcessor

# Search
from search.search_engine import SearchEngine
from search.rag_system import RAGSystem
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each directory has a specific purpose
2. **Python Package Standards**: Follows Python packaging best practices
3. **Scalability**: Easy to add new modules or split existing ones
4. **Testability**: Clear test organization parallel to source structure
5. **Import Clarity**: Explicit import paths make dependencies obvious
6. **Modularity**: Components can be easily reused or replaced

## Migration Notes

- All imports have been updated to use the new package structure
- Original files have been moved to appropriate subdirectories
- Entry points have been created for different use cases
- Legacy scripts remain in the root for backward compatibility during transition

## Next Steps

1. Test the complete system with the new structure
2. Update deployment scripts to use new entry points
3. Create comprehensive documentation for each module
4. Set up proper testing infrastructure