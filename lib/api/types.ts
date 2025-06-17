/**
 * TypeScript type definitions for RAG Document Chat API
 * Based on the backend Pydantic models
 */

// Search Types
export interface SearchRequest {
  query: string;
  top_k?: number;
  collections?: string[];
  documents?: string[];
  exclude_documents?: string[];
  threshold?: number;
  return_chunks?: boolean;
}

export interface SearchResult {
  content: string;
  score: number;
  document: string;
  chunk_id: string;
  collection: string;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  search_id: string;
  query: string;
  total_results: number;
  unique_documents: string[];
  chunk_ids: string[];
  processing_time: number;
  collections_searched: string[];
}

// Question Answering Types
export interface AskRequest {
  question: string;
  top_k?: number;
  documents?: string[];
  exclude_documents?: string[];
  chunk_ids?: string[];
  search_id?: string;
  conversation_history?: string;
  search_strategy?: 'basic' | 'enhanced' | 'paragraph';
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  processing_time: number;
}

// Document Types
export interface DocumentResponse {
  status: string;
  message: string;
  chunks_created?: number;
  processing_time?: number;
}

export interface DocumentInfo {
  name: string;
  chunks: number;
  status: 'processed' | 'processing' | 'error';
  size: string;
  collections: Record<string, number>;
  total_chunks: number;
}

export interface DocumentsResponse {
  documents: Record<string, DocumentInfo>;
  total_items: number;
  collections: CollectionInfo[];
}

// System Types
export interface SystemStatus {
  chromadb: string;
  ollama: string;
  api: string;
  documents: number;
  collections: number;
}

export interface CollectionInfo {
  name: string;
  count: number;
  unique_documents?: string[];
  sample_ids?: string[];
}

export interface CollectionsInfo {
  collections: CollectionInfo[];
  total_collections: number;
}

// UI State Types
export interface UploadProgress {
  progress: number;
  isUploading: boolean;
  filename?: string;
}

export interface SearchContext {
  query: string;
  results: number;
  documents: string[];
  search_id?: string;
}

export interface SystemHealth {
  healthy: boolean;
  services?: SystemStatus;
  error?: string;
  timestamp: string;
}

// Error Types
export interface ApiError {
  message: string;
  status?: number;
  timestamp: string;
}