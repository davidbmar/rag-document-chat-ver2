/**
 * TypeScript REST API Client for RAG Document Chat System
 * Adapted from the existing JavaScript client for ui.tsx integration
 */

import { config } from './config';
import type {
  SearchRequest,
  SearchResponse,
  AskRequest,
  ChatResponse,
  DocumentResponse,
  SystemStatus,
  CollectionsInfo
} from './types';

class RAGApiClient {
  private baseUrl: string;
  private timeout: number;
  private debugMode: boolean;

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
  private async request<T>(method: string, endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      if (this.debugMode) {
        console.log(`API ${method} ${endpoint}:`, options.body);
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
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      
      if (this.debugMode) {
        console.error(`API Error ${method} ${endpoint}:`, error);
      }
      
      // Handle network errors more gracefully
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw new Error(`Connection failed. Please ensure the API server is running at ${this.baseUrl}`);
      }
      
      throw error;
    }
  }

  private async get<T>(endpoint: string, params: Record<string, string> = {}): Promise<T> {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request<T>('GET', url);
  }

  private async post<T>(endpoint: string, data: any = {}): Promise<T> {
    return this.request<T>('POST', endpoint, {
      body: JSON.stringify(data)
    });
  }

  private async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>('POST', endpoint, {
      body: formData,
      headers: {} // Remove Content-Type for FormData
    });
  }

  private async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint);
  }

  // Search Operations
  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.post<SearchResponse>('/api/search', request);
  }

  // Question Answering
  async ask(request: AskRequest): Promise<ChatResponse> {
    return this.post<ChatResponse>('/api/ask', request);
  }

  // Document Management
  async getDocuments() {
    return this.get('/api/documents');
  }

  async uploadDocument(file: File, force: boolean = false): Promise<DocumentResponse> {
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

    return this.postForm<DocumentResponse>('/api/process/upload', formData);
  }

  async clearDocuments() {
    return this.delete('/api/documents');
  }

  // Document Processing
  async processDocumentSummaries(filename: string): Promise<DocumentResponse> {
    return this.post<DocumentResponse>(`/api/process/${encodeURIComponent(filename)}/summaries`);
  }

  async processDocumentParagraphs(filename: string): Promise<DocumentResponse> {
    return this.post<DocumentResponse>(`/api/process/${encodeURIComponent(filename)}/paragraphs`);
  }

  // Collections
  async getCollections(): Promise<CollectionsInfo> {
    return this.get<CollectionsInfo>('/api/collections');
  }

  // System Status
  async getStatus(): Promise<SystemStatus> {
    return this.get<SystemStatus>('/status');
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
        error: error instanceof Error ? error.message : 'Unknown error',
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
export const apiClient = new RAGApiClient();
export default apiClient;