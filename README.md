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

- Linux/Ubuntu server (tested on Ubuntu 20.04+)
- Python 3.9+
- Docker and Docker Compose
- OpenAI API key
- AWS credentials (optional, for S3 storage)

## 🛠️ Quick Setup (Recommended)

### For New EC2/Ubuntu Servers

1. **Clone and run automated setup**
   ```bash
   git clone https://github.com/davidbmar/rag-document-chat-ver2.git
   cd rag-document-chat-ver2
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. **Configure your API keys**
   ```bash
   nano .env
   # Replace KEYHERE with your actual OpenAI API key
   # Configure AWS credentials if using S3
   ```

3. **Start the application**
   ```bash
   ./start.sh
   ```

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/davidbmar/rag-document-chat-ver2.git
   cd rag-document-chat-ver2
   ```

2. **Install system dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv docker.io docker-compose
   ```

3. **Set up Python environment**
   ```bash
   python3 -m venv rag_env
   source rag_env/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp sample.env.txt .env
   # Edit .env with your API keys and settings
   ```

5. **Start ChromaDB**
   ```bash
   docker-compose up -d chromadb
   ```

6. **Download NLTK data**
   ```bash
   python3 -c "import nltk; nltk.download('punkt')"
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

### Quick Start
```bash
./start.sh
```

Choose from 5 options:
1. **Web Interface** (Streamlit) - Interactive document chat
2. **API Server** (FastAPI) - REST API for integration
3. **Modern UI** (Next.js) - Beautiful shadcn/ui interface with full API integration
4. **Both interfaces** - Run simultaneously
5. **Background mode** - Run as daemon services

### Manual Commands

#### Web Interface (Streamlit)
```bash
source rag_env/bin/activate
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

#### API Server (FastAPI)
```bash
source rag_env/bin/activate
python3 app_refactored.py
```

#### Modern UI (Next.js)
```bash
# Install Node.js dependencies (first time only)
cd src/ui/modern && npm install

# Start the development server
npm run dev
```

#### RAG CLI (Executable)
```bash
# Can be run from anywhere in the project
./rag search "your query"
./rag ask "your question"
./rag list
./rag status
```

### Access URLs
- **Web Interface**: http://localhost:8501 (or your-server-ip:8501)
- **Modern UI**: http://localhost:3004 (or your-server-ip:3004)
- **API Server**: http://localhost:8000 (or your-server-ip:8000)
- **API Documentation**: http://localhost:8000/docs

### Document Processing Workflow

1. **Upload Document** - PDF or TXT files
2. **Basic Processing** - Creates logical chunks and metadata
3. **Smart Summaries** (Optional) - Generates 10:1 compressed logical summaries
4. **Paragraph Context** (Optional) - Creates 3:1 compressed paragraph summaries
5. **Chat** - Ask questions using the best available search method

## 🖥️ CLI Usage

The `rag` executable provides a powerful command-line interface to the RAG system:

### Basic Commands
```bash
# Search documents
./rag search "vacation policy"
./rag search "database backup procedures"

# Ask questions
./rag ask "How many vacation days do employees get?"
./rag ask "Can employees work remotely?"

# System management
./rag list                    # List all documents
./rag status                  # Check system health
./rag collections             # View collections info
./rag clear                   # Clear all documents
```

### Advanced Usage
```bash
# Filtered search
./rag search "policy" --documents company_policy.txt
./rag search "backup" --exclude alice.txt

# Search strategies
./rag ask "remote work" --strategy enhanced
./rag ask "warranty info" --strategy paragraph

# Interactive mode
./rag ask "hello" --interactive

# Save and reuse search results
./rag search "vacation" --save vacation_search.json
./rag ask "How many days?" --from-search vacation_search.json
```

### Document Processing
```bash
# Upload new documents
./rag process upload test_documents/new_policy.txt

# Generate enhanced summaries
./rag process summaries company_policy.txt
./rag process paragraphs technical_manual.txt
```

The CLI automatically handles:
- ✅ **Virtual environment** - Works without manual activation
- ✅ **Path resolution** - Can be run from any subdirectory
- ✅ **API connectivity** - Connects to local API server
- ✅ **Error handling** - Clear error messages and graceful failures

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

## ☁️ EC2 Deployment Notes

### Security Group Configuration
For external access, configure your EC2 security group to allow:
- **Port 8501** (Streamlit Web Interface)
- **Port 3004** (Modern Next.js UI)
- **Port 8000** (FastAPI Server)
- **Port 22** (SSH access)
- **Port 8002** (ChromaDB - internal only, not needed for external access)

### Firewall Commands (if using UFW)
```bash
sudo ufw allow 8501/tcp
sudo ufw allow 3004/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
```

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