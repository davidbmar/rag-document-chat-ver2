/**
 * REST API Client for RAG Document Chat System
 * Environment-configurable, REST-only implementation
 */

import config from './config.js';

class RAGApiClient {
  constructor() {
    this.baseUrl = config.apiBaseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.apiTimeout;
    this.debugMode = config.debugMode;
    
    if (this.debugMode) {
      console.log('RAG API Client initialized:', {
        baseUrl: this.baseUrl,
        timeout: this.timeout
      });
    }
  }

  // Base HTTP Methods
  async request(method, endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      if (this.debugMode) {
        console.log(`API ${method} ${endpoint}:`, options.body || options.params);
      }

      const response = await fetch(url, {
        method,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // Response not JSON, use status text
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      if (this.debugMode) {
        console.log(`API Response ${method} ${endpoint}:`, data);
      }

      return data;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      
      if (this.debugMode) {
        console.error(`API Error ${method} ${endpoint}:`, error);
      }
      
      throw error;
    }
  }

  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request('GET', url);
  }

  async post(endpoint, data = {}) {
    return this.request('POST', endpoint, {
      body: JSON.stringify(data)
    });
  }

  async postForm(endpoint, formData) {
    return this.request('POST', endpoint, {
      body: formData,
      headers: {} // Remove Content-Type for FormData
    });
  }

  async delete(endpoint) {
    return this.request('DELETE', endpoint);
  }

  // Search Operations
  async search(query, options = {}) {
    const payload = {
      query,
      top_k: options.topK || config.defaultTopK,
      return_chunks: true,
      ...options.filters
    };

    return this.post('/api/search', payload);
  }

  // Question Answering
  async ask(question, options = {}) {
    const payload = {
      question,
      top_k: options.topK || config.defaultTopK,
      conversation_history: options.history || '',
      search_strategy: options.strategy || 'enhanced'
    };

    // Add context if provided
    if (options.searchId) {
      payload.search_id = options.searchId;
    } else if (options.documents) {
      payload.documents = options.documents;
    } else if (options.chunkIds) {
      payload.chunk_ids = options.chunkIds;
    }

    return this.post('/api/ask', payload);
  }

  // Document Management
  async getDocuments() {
    return this.get('/api/documents');
  }

  async uploadDocument(file, force = false) {
    // Validate file before upload
    if (!config.isFileTypeAllowed(file.name)) {
      throw new Error(`File type not allowed. Allowed types: ${config.allowedFileTypes.join(', ')}`);
    }

    if (!config.isFileSizeAllowed(file.size)) {
      throw new Error(`File too large. Maximum size: ${config.getMaxFileSizeFormatted()}`);
    }

    const formData = new FormData();
    formData.append('file', file);
    if (force) {
      formData.append('force', 'true');
    }

    return this.postForm('/api/process/upload', formData);
  }

  async clearDocuments() {
    return this.delete('/api/documents');
  }

  // Document Processing
  async processDocumentSummaries(filename) {
    return this.post(`/api/process/${encodeURIComponent(filename)}/summaries`);
  }

  async processDocumentParagraphs(filename) {
    return this.post(`/api/process/${encodeURIComponent(filename)}/paragraphs`);
  }

  // Collections
  async getCollections() {
    return this.get('/api/collections');
  }

  // System Status
  async getStatus() {
    return this.get('/status');
  }

  // Health Check
  async healthCheck() {
    try {
      const status = await this.getStatus();
      return {
        healthy: true,
        services: status,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        healthy: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  // Utility Methods
  getApiInfo() {
    return {
      baseUrl: this.baseUrl,
      timeout: this.timeout,
      maxFileSize: config.getMaxFileSizeFormatted(),
      allowedTypes: config.allowedFileTypes,
      environment: config.isDevelopment ? 'development' : 'production'
    };
  }
}

// Export singleton instance
export default new RAGApiClient();