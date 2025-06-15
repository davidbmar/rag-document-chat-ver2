# RAG System Utilities

## working_cli.py

A lightweight CLI utility that provides direct access to the RAG system for testing and development.

### Usage

```bash
# Search documents
python3 scripts/utils/working_cli.py search "your query here"

# Ask questions
python3 scripts/utils/working_cli.py ask "your question here"
```

### Examples

```bash
# Search for vacation policy information
python3 scripts/utils/working_cli.py search "vacation policy"

# Ask specific questions
python3 scripts/utils/working_cli.py ask "How many vacation days do employees get?"
python3 scripts/utils/working_cli.py ask "Can employees work remotely?"
python3 scripts/utils/working_cli.py ask "What time are database backups performed?"
```

### Features

- Direct access to RAG system without API layer
- Semantic search with vector embeddings
- Context-aware question answering
- Multi-document search and retrieval
- Source attribution for answers

### Requirements

- RAG system must be initialized with documents
- ChromaDB running on localhost:8002
- OpenAI API key configured in .env file