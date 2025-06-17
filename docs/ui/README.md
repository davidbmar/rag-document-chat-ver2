# RAG Document Chat UI

A modern Next.js interface for the RAG Document Chat System with beautiful shadcn/ui components and full REST API integration.

## 🏗️ Architecture

### **Environment-Driven Configuration**
- All API endpoints and settings configured via environment variables
- Separate configs for development, production, and local overrides
- No hardcoded URLs or ports

### **REST-Only Design**
- Complete separation from backend logic
- All communication via HTTP REST API calls
- Fully stateless and scalable

### **Tab-Based Navigation**
- **🔍 Search**: Find information across documents
- **💬 Ask**: Conversational Q&A with source tracking
- **📚 Browse**: Document management and upload
- **⚙️ Status**: System health and statistics

## 🚀 Quick Start

### **Prerequisites**
- Node.js 16+ and npm
- RAG API server running (default: http://localhost:8000)

### **Installation**
```bash
# Navigate to UI directory
cd src/ui

# Install dependencies
npm install

# Start development server
npm run dev
```

### **Environment Configuration**
```bash
# Copy example environment
cp .env.example .env.local

# Edit configuration (Next.js uses different environment variables)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_MAX_FILE_SIZE=50000000
NEXT_PUBLIC_ALLOWED_FILE_TYPES=.pdf,.txt
```

## 🔧 Environment Variables

### **Required**
- `NEXT_PUBLIC_API_BASE_URL`: API server base URL (set automatically via proxy in development)

### **Optional**
- `NEXT_PUBLIC_API_TIMEOUT`: Request timeout (default: 30000ms)
- `NEXT_PUBLIC_MAX_FILE_SIZE`: Max upload size (default: 50MB)
- `NEXT_PUBLIC_ALLOWED_FILE_TYPES`: Allowed file extensions
- `NEXT_PUBLIC_DEFAULT_TOP_K`: Default search result count
- `NEXT_PUBLIC_DEBUG_MODE`: Enable debug logging

## 📁 Project Structure

```
src/ui/
├── components/ui/             # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── tabs.tsx
│   └── ...
├── lib/
│   ├── api/
│   │   ├── client.ts          # TypeScript API client
│   │   ├── config.ts          # Environment configuration
│   │   └── types.ts           # API type definitions
│   └── utils/
│       └── errorHandler.ts    # Error handling utilities
├── pages/
│   ├── index.tsx              # Main page entry point
│   └── api/proxy/[...path].ts # API proxy for CORS
├── styles/
│   └── globals.css            # Tailwind CSS with shadcn/ui design tokens
├── ui.tsx                     # Main UI component
├── next.config.js             # Next.js configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── postcss.config.js          # PostCSS configuration
└── package.json               # Dependencies and scripts
```

## 🎯 Key Features

### **Search Tab**
- Natural language search across all documents
- Advanced filtering by document, collection, confidence
- Results with source citations and confidence scores
- One-click transition to Ask tab with context

### **Ask Tab**
- Conversational Q&A interface
- Context configuration (documents, search results, strategy)
- Source tracking with click-to-view functionality
- Conversation history with timestamps

### **Browse Tab**
- Drag & drop file upload with progress tracking
- Document library with processing status
- Collection browser with statistics
- Quick actions (search this document, ask questions)

### **Status Tab**
- Real-time system health monitoring
- Document and collection statistics
- Configuration display
- System management actions

## 🔄 Cross-Tab Workflows

### **Search → Ask**
```
Search for "vacation policy" → View results → "Ask About This" → Ask tab with context
```

### **Ask → Browse**
```
Get answer with sources → "View Sources" → Browse tab highlighting documents
```

### **Browse → Search**
```
View document in library → "Search This" → Search tab filtered to that document
```

## 🛠️ Development

### **Start Development Server**
```bash
# Start with environment
./scripts/start-ui.sh development

# Or directly
cd src/ui && npm start
```

### **Build for Production**
```bash
# Build with environment
./scripts/start-ui.sh production build

# Or directly
cd src/ui && npm run build:prod
```

### **Environment-Specific Commands**
```bash
npm run start:dev      # Development with dev config
npm run start:prod     # Production mode locally
npm run build:dev      # Development build
npm run build:prod     # Production build
```

## 🔧 Configuration Examples

### **Development (.env.development)**
```env
REACT_APP_API_BASE_URL=http://localhost:8003
REACT_APP_DEBUG_MODE=true
REACT_APP_MAX_FILE_SIZE=50000000
```

### **Production (.env.production)**
```env
REACT_APP_API_BASE_URL=https://api.rag-system.com
REACT_APP_DEBUG_MODE=false
REACT_APP_MAX_FILE_SIZE=100000000
```

### **Local Override (.env.local)**
```env
# Override any setting for local development
REACT_APP_API_BASE_URL=http://192.168.1.100:8003
REACT_APP_DEBUG_MODE=true
```

## 🚀 Deployment

### **Static Hosting**
```bash
# Build production version
npm run build:prod

# Deploy build/ directory to any static host
```

### **Docker**
```dockerfile
FROM nginx:alpine
COPY build/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### **Environment at Runtime**
For Docker deployments, environment variables can be injected at runtime using build-time arguments or runtime configuration.

## 🐛 Troubleshooting

### **API Connection Issues**
1. Check `REACT_APP_API_BASE_URL` in environment
2. Verify API server is running: `curl $API_URL/status`
3. Check browser console for CORS errors
4. Ensure API server allows cross-origin requests

### **Upload Issues**
1. Check file size limits: `REACT_APP_MAX_FILE_SIZE`
2. Verify file types: `REACT_APP_ALLOWED_FILE_TYPES`
3. Check API server upload endpoint
4. Monitor network tab for upload progress

### **Performance Issues**
1. Reduce `REACT_APP_DEFAULT_TOP_K` for faster searches
2. Increase `REACT_APP_API_TIMEOUT` for large uploads
3. Enable `REACT_APP_DEBUG_MODE` to monitor API calls
4. Check API server performance

## 📚 API Integration

The UI communicates exclusively through REST endpoints:

```javascript
// Search documents
POST /api/search
{
  "query": "vacation policy",
  "top_k": 10,
  "collections": ["documents"],
  "threshold": 0.7
}

// Ask questions
POST /api/ask  
{
  "question": "How many vacation days?",
  "search_id": "uuid",
  "top_k": 8
}

// Upload documents
POST /api/process/upload
FormData: { file: File, force: boolean }

// Get system status
GET /status
```

All responses include proper error handling and status codes for robust client-side error management.