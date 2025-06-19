/**
 * Configuration manager for RAG UI
 * Handles environment variables and provides defaults
 */

class Config {
  constructor() {
    this.validateEnvironment();
  }

  // API Configuration
  get apiBaseUrl() {
    return process.env.REACT_APP_API_BASE_URL || 'http://localhost:8003';
  }

  get apiTimeout() {
    return parseInt(process.env.REACT_APP_API_TIMEOUT || '30000');
  }

  // File Upload Configuration
  get maxFileSize() {
    return parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '50000000'); // 50MB default
  }

  get allowedFileTypes() {
    const types = process.env.REACT_APP_ALLOWED_FILE_TYPES || '.pdf,.txt';
    return types.split(',').map(type => type.trim());
  }

  // Search Defaults
  get defaultTopK() {
    return parseInt(process.env.REACT_APP_DEFAULT_TOP_K || '10');
  }

  get defaultConfidenceThreshold() {
    return parseFloat(process.env.REACT_APP_DEFAULT_CONFIDENCE_THRESHOLD || '0.7');
  }

  // System Settings
  get pollingInterval() {
    return parseInt(process.env.REACT_APP_POLLING_INTERVAL || '30000');
  }

  get debugMode() {
    return process.env.REACT_APP_DEBUG_MODE === 'true';
  }

  // Environment Detection
  get isDevelopment() {
    return process.env.NODE_ENV === 'development';
  }

  get isProduction() {
    return process.env.NODE_ENV === 'production';
  }

  // Validation
  validateEnvironment() {
    const required = ['REACT_APP_API_BASE_URL'];
    const missing = required.filter(key => !process.env[key]);
    
    if (missing.length > 0 && this.isProduction) {
      console.warn('Missing required environment variables:', missing);
    }

    // Validate API URL format
    try {
      new URL(this.apiBaseUrl);
    } catch (error) {
      throw new Error(`Invalid API base URL: ${this.apiBaseUrl}`);
    }

    if (this.debugMode) {
      console.log('RAG UI Configuration:', {
        apiBaseUrl: this.apiBaseUrl,
        environment: process.env.NODE_ENV,
        maxFileSize: this.maxFileSize,
        allowedTypes: this.allowedFileTypes
      });
    }
  }

  // Helper Methods
  formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  getMaxFileSizeFormatted() {
    return this.formatFileSize(this.maxFileSize);
  }

  isFileTypeAllowed(filename) {
    const extension = '.' + filename.split('.').pop().toLowerCase();
    return this.allowedFileTypes.includes(extension);
  }

  isFileSizeAllowed(fileSize) {
    return fileSize <= this.maxFileSize;
  }
}

// Export singleton instance
export default new Config();