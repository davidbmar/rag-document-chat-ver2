# RAG Document Chat System v2

A modular, production-ready Retrieval-Augmented Generation (RAG) system for intelligent document chat with hierarchical processing and paragraph-aware search.

## 🚀 Features

### Multi-Layer Document Processing
- **📄 Basic Chunks**: Logical document chunking with metadata extraction
- **🧠 Smart Summaries**: 10:1 compressed hierarchical summaries for logical understanding
- **📝 Paragraph Context**: 3:1 compressed natural paragraph summaries for wider search context

### Intelligent Search Hierarchy
The system automatically selects the best search strategy:
1. **Paragraph Context** - Uses natural paragraph boundaries for wider contextual understanding
2. **Smart Summaries** - Leverages logical groupings with 10:1 compression for conceptual search
3. **Basic Chunks** - Falls back to detailed document chunks for specific information

### Production-Ready Architecture
- **Modular Design**: 9 focused modules replacing monolithic architecture
- **Robust Configuration**: Environment-based config with validation and demo mode
- **Error Handling**: Comprehensive logging and graceful fallbacks
- **Type Safety**: Full Pydantic models and dataclasses
- **Scalable Storage**: ChromaDB vector storage with S3 document persistence

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- AWS credentials (optional, for S3 storage)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/davidbmar/rag-document-chat-ver2.git
   cd rag-document-chat-ver2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp sample.env.txt .env
   # Edit .env with your API keys and settings
   ```

4. **Download NLTK data** (automatic on first run)
   ```bash
   python -c "import nltk; nltk.download('punkt')"
   ```

## ⚙️ Configuration

Create a `.env` file with your settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Application Settings
DEMO_MODE=false
LOG_LEVEL=INFO
```

## 🚀 Usage

### Web Interface (Streamlit)
```bash
python streamlit_app.py
```

### API Server (FastAPI)
```bash
python app_refactored.py
```

### Document Processing Workflow

1. **Upload Document** - PDF or TXT files
2. **Basic Processing** - Creates logical chunks and metadata
3. **Smart Summaries** (Optional) - Generates 10:1 compressed logical summaries
4. **Paragraph Context** (Optional) - Creates 3:1 compressed paragraph summaries
5. **Chat** - Ask questions using the best available search method

## 🏗️ Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `config.py` | Environment configuration and validation |
| `models.py` | Pydantic models and dataclasses |
| `clients.py` | External service wrappers (OpenAI, ChromaDB, S3) |
| `text_processing.py` | Document chunking and metadata extraction |
| `document_processor.py` | Document processing orchestration |
| `search_engine.py` | Multi-strategy search with paragraph awareness |
| `hierarchical_processor.py` | 10:1 compression logical summaries |
| `paragraph_processor.py` | Natural paragraph processing |
| `rag_system.py` | Main coordinator integrating all components |
| `utils.py` | Logging and utility functions |

### Entry Points

- `streamlit_app.py` - Interactive web interface
- `app_refactored.py` - FastAPI REST API server

## 🔍 Search Strategies

The system intelligently selects search strategies based on available processing:

### 1. Paragraph Context Search
- **When**: Paragraph summaries are available
- **How**: Searches 3:1 compressed paragraph summaries + detailed chunks
- **Best for**: Questions requiring broader context and thematic understanding

### 2. Enhanced Search (Smart Summaries)
- **When**: Logical summaries are available (no paragraphs)
- **How**: Combines 10:1 compressed summaries with detailed chunks
- **Best for**: Conceptual questions and logical reasoning

### 3. Basic Search
- **When**: Only basic chunks are available
- **How**: Direct search on document chunks
- **Best for**: Specific fact-finding and detailed information

## 📊 Processing Statistics

Each processing step provides detailed metrics:

- **Compression ratios** (10:1 for summaries, 3:1 for paragraphs)
- **Word count reductions**
- **Processing times**
- **Storage efficiency**

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

The system includes:
- ChromaDB vector database
- Streamlit web interface
- FastAPI backend
- Persistent storage volumes

## 📝 API Endpoints

### Document Processing
- `POST /upload` - Upload and process document
- `POST /process-hierarchical/{filename}` - Add smart summaries
- `POST /process-paragraphs/{filename}` - Add paragraph context

### Search & Chat
- `POST /search` - Basic document search
- `POST /search-enhanced` - Enhanced search with summaries
- `POST /search-paragraphs` - Paragraph-aware search
- `POST /chat` - Interactive chat with documents

### System
- `GET /health` - System health check
- `GET /status` - Service status overview

## 🔧 Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Type checking
mypy .

# Linting
flake8 .

# Formatting
black .
```

## 🔒 Security Features

- **Environment-based secrets** management
- **Input validation** with Pydantic models
- **Secure file handling** with type checking
- **Demo mode** for development without API keys
- **Comprehensive logging** for audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code quality checks pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙋 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review logs for troubleshooting

---

**Built with ❤️ using Python, OpenAI, ChromaDB, and Streamlit**