# Configuration Guide

The RAG Document Chat system uses environment variables for configuration, loaded from a `.env` file.

## Quick Setup

1. Copy the sample configuration:
   ```bash
   cp sample.env.txt .env
   ```

2. Edit `.env` with your values:
   ```bash
   nano .env
   ```

3. Set your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

## Configuration Options

### API Server Settings
```bash
# API Server Configuration
API_HOST=0.0.0.0      # Host to bind to (0.0.0.0 for all interfaces)
API_PORT=8003         # Port for the API server
```

### OpenAI Settings
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...           # Your OpenAI API key
EMBEDDING_MODEL=text-embedding-ada-002  # Embedding model
CHAT_MODEL=gpt-3.5-turbo       # Chat model for responses
```

### ChromaDB Settings
```bash
# ChromaDB Configuration
CHROMA_HOST=localhost    # ChromaDB host
CHROMA_PORT=8002        # ChromaDB port
```

### AWS S3 Settings (Optional)
```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-2
S3_BUCKET=your-bucket-name
```

### Processing Settings
```bash
# Processing Configuration
CHUNK_SIZE=1000          # Document chunk size
CHUNK_OVERLAP=100        # Overlap between chunks
MAX_CHUNKS=15           # Maximum chunks to use in responses
```

## Usage Examples

### Different Ports
To run on a different port, edit `.env`:
```bash
API_PORT=9000
```

Then restart the server:
```bash
python3 app_refactored.py api
```

The CLI will automatically use the configured port:
```bash
python3 cli.py status
```

### Different Host
For external access, set:
```bash
API_HOST=0.0.0.0    # Accept connections from any IP
```

For local only:
```bash
API_HOST=127.0.0.1  # Local connections only
```

### Demo Mode
If you don't have an OpenAI API key:
```bash
DEMO_MODE=true
```

## Verification

Check your configuration:
```bash
python3 -c "from config import config; print(f'API URL: {config.api_url}')"
```

Test the system:
```bash
python3 cli.py status
```

## Troubleshooting

### Port Already in Use
If you get "Address already in use" error:
1. Change `API_PORT` in `.env`
2. Restart the server
3. CLI will automatically use the new port

### API Connection Refused
1. Check if the server is running
2. Verify the port in `.env` matches the running server
3. Check firewall settings if accessing remotely

### OpenAI API Errors
1. Verify your API key is correct
2. Check your OpenAI account has credits
3. Set `DEMO_MODE=true` for testing without API key