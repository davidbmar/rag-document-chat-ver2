/**
 * Configuration for RAG Document Chat API Client
 */

interface ApiConfig {
  apiBaseUrl: string;
  apiTimeout: number;
  debugMode: boolean;
  isDevelopment: boolean;
  defaultTopK: number;
  allowedFileTypes: string[];
  maxFileSize: number;
  
  isFileTypeAllowed(filename: string): boolean;
  isFileSizeAllowed(size: number): boolean;
  getMaxFileSizeFormatted(): string;
}

const createConfig = (): ApiConfig => {
  // Environment detection
  const isDevelopment = process.env.NODE_ENV === 'development' || 
                       (typeof window !== 'undefined' && window.location.hostname === 'localhost');
  
  // API Base URL - use proxy approach to avoid CORS issues
  let apiBaseUrl: string;
  if (typeof window !== 'undefined') {
    // Client-side: use proxy through Next.js to avoid CORS
    apiBaseUrl = '/api/proxy';
  } else {
    // Server-side: use localhost
    apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  }

  return {
    apiBaseUrl,
    apiTimeout: 30000, // 30 seconds
    debugMode: isDevelopment,
    isDevelopment,
    defaultTopK: 10,
    allowedFileTypes: ['.pdf', '.txt', '.png', '.jpg', '.jpeg'],
    maxFileSize: 50 * 1024 * 1024, // 50MB in bytes

    isFileTypeAllowed(filename: string): boolean {
      const extension = '.' + filename.split('.').pop()?.toLowerCase();
      return this.allowedFileTypes.includes(extension || '');
    },

    isFileSizeAllowed(size: number): boolean {
      return size <= this.maxFileSize;
    },

    getMaxFileSizeFormatted(): string {
      const mb = this.maxFileSize / (1024 * 1024);
      return `${mb}MB`;
    }
  };
};

export const config = createConfig();