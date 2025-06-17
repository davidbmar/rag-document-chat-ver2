/**
 * Error handling utilities for RAG Document Chat UI
 */

import type { ApiError } from '../api/types';

export class RAGError extends Error {
  public status?: number;
  public timestamp: string;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'RAGError';
    this.status = status;
    this.timestamp = new Date().toISOString();
  }
}

export const handleApiError = (error: unknown): ApiError => {
  if (error instanceof RAGError) {
    return {
      message: error.message,
      status: error.status,
      timestamp: error.timestamp
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      timestamp: new Date().toISOString()
    };
  }

  return {
    message: 'An unknown error occurred',
    timestamp: new Date().toISOString()
  };
};

export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unknown error occurred';
};

export const isNetworkError = (error: unknown): boolean => {
  if (error instanceof Error) {
    return error.message.includes('timeout') ||
           error.message.includes('network') ||
           error.message.includes('fetch');
  }
  return false;
};

export const formatErrorForUser = (error: unknown): string => {
  const message = getErrorMessage(error);
  
  if (isNetworkError(error)) {
    return 'Connection failed. Please check your network and try again.';
  }
  
  if (message.includes('timeout')) {
    return 'Request timed out. The server may be busy, please try again.';
  }
  
  if (message.includes('File too large')) {
    return message; // Show file size errors as-is
  }
  
  if (message.includes('File type not allowed')) {
    return message; // Show file type errors as-is
  }
  
  // Generic error for API errors
  if (message.includes('HTTP')) {
    return 'Server error occurred. Please try again or contact support.';
  }
  
  return message;
};