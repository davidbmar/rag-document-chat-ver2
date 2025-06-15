# Directory Structure Analysis and Reorganization Plan

## Current Structure Issues

### Problems with Current Layout:
1. **All files in root** - 30+ files mixed together
2. **No logical grouping** - Core code mixed with tests, scripts, docs
3. **Unclear entry points** - Multiple main files (`app_refactored.py`, `cli.py`, `streamlit_app.py`)
4. **Test files scattered** - Tests mixed with core code
5. **Scripts everywhere** - Setup, production, and utility scripts in root
6. **Unclear imports** - No package structure

## Proposed New Structure

```
rag-document-chat-ver2/
├── README.md                   # Main project documentation
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker services
├── .env.example               # Environment template
│
├── src/                       # Main application code
│   ├── __init__.py
│   ├── main.py               # Main entry point (replaces app_refactored.py)
│   ├── cli.py                # CLI entry point
│   │
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── models.py         # Data models
│   │   ├── clients.py        # External service clients
│   │   └── utils.py          # Utility functions
│   │
│   ├── processing/           # Document processing modules
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   ├── hierarchical_processor.py
│   │   ├── paragraph_processor.py
│   │   └── text_processing.py
│   │
│   ├── search/              # Search and RAG functionality
│   │   ├── __init__.py
│   │   ├── search_engine.py
│   │   └── rag_system.py
│   │
│   ├── api/                 # FastAPI application
│   │   ├── __init__.py
│   │   ├── app.py           # FastAPI app definition
│   │   ├── endpoints/       # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── search.py    # Search endpoints
│   │   │   ├── documents.py # Document endpoints
│   │   │   └── system.py    # System endpoints
│   │   └── middleware/      # API middleware
│   │       └── __init__.py
│   │
│   └── ui/                  # User interfaces
│       ├── __init__.py
│       └── streamlit_app.py # Streamlit interface
│
├── tests/                   # All tests
│   ├── __init__.py
│   ├── unit/               # Unit tests
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   └── test_processors.py
│   ├── integration/        # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   └── test_workflows.py
│   └── acceptance/         # Acceptance tests
│       ├── __init__.py
│       └── mvp_acceptance_test.py
│
├── scripts/                # Utility and deployment scripts
│   ├── setup.sh           # Initial setup
│   ├── start.sh           # Quick start
│   ├── production/        # Production scripts
│   │   ├── setup.sh       # Production setup
│   │   ├── monitor.sh     # Monitoring
│   │   └── test.sh        # Production testing
│   ├── development/       # Development scripts
│   │   ├── demo_workflow.sh
│   │   └── cleanup.sh
│   └── utils/             # Utility scripts
│       ├── cleanup_chroma_ports.sh
│       └── s3_debug_script.sh
│
├── docs/                   # Documentation
│   ├── README.md          # Detailed documentation
│   ├── CONFIGURATION.md   # Configuration guide
│   ├── DEPLOYMENT.md      # Deployment guide
│   ├── API.md            # API documentation
│   └── DEVELOPMENT.md    # Development guide
│
├── config/                # Configuration files
│   ├── sample.env        # Environment template
│   └── docker/           # Docker configurations
│       └── docker-compose.yml
│
└── data/                  # Data directory (gitignored)
    ├── uploads/          # Uploaded documents
    ├── cache/            # Cache files
    └── logs/             # Log files
```

## Benefits of New Structure

### 1. **Clear Separation of Concerns**
- Core logic in `src/core/`
- Processing modules in `src/processing/`
- API code in `src/api/`
- Tests in `tests/`
- Scripts in `scripts/`

### 2. **Proper Python Package Structure**
- Each directory has `__init__.py`
- Clean import paths: `from src.core.config import config`
- Modular and testable

### 3. **Logical Grouping**
- Related files together
- Clear entry points (`src/main.py`, `src/cli.py`)
- Environment-specific scripts separated

### 4. **Scalability**
- Easy to add new modules
- Clear where new files should go
- Supports team development

### 5. **Professional Standards**
- Follows Python packaging conventions
- Separates source, tests, docs, scripts
- Production-ready structure

## Migration Strategy

### Phase 1: Create Directory Structure
1. Create all directories with `__init__.py` files
2. Move files to appropriate locations
3. Update imports throughout codebase

### Phase 2: Update Entry Points
1. Create `src/main.py` as primary entry point
2. Update CLI to use new structure
3. Update API module organization

### Phase 3: Fix Dependencies
1. Update all import statements
2. Update scripts to use new paths
3. Update Docker and deployment configs

### Phase 4: Update Documentation
1. Update README with new structure
2. Update all documentation files
3. Create development guide

### Phase 5: Test and Validate
1. Run all tests
2. Verify CLI works
3. Verify API works
4. Test production deployment

## Implementation Notes

### Import Changes Required:
```python
# Old imports
from config import config
from models import ChatRequest
from rag_system import RAGSystem

# New imports  
from src.core.config import config
from src.core.models import ChatRequest
from src.search.rag_system import RAGSystem
```

### Entry Point Changes:
```bash
# Old entry points
python app_refactored.py api
python cli.py search "query"
python streamlit_app.py

# New entry points
python -m src.main api
python -m src.cli search "query"  
python -m src.ui.streamlit_app
```

### Docker Updates:
```dockerfile
# Update WORKDIR and entry points in Docker
WORKDIR /app
CMD ["python", "-m", "src.main", "api"]
```

This structure provides a solid foundation for scaling the project and maintaining code quality as we add more features in Step 2 and beyond.