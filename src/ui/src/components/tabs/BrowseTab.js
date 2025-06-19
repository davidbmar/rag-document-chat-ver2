/**
 * Browse Tab Component
 * Document management and upload interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '../../api/client.js';
import config from '../../api/config.js';
import LoadingSpinner from '../common/LoadingSpinner.js';
import ErrorDisplay from '../common/ErrorDisplay.js';
import './BrowseTab.css';

const BrowseTab = ({ 
  context, 
  onSwitchToSearch, 
  onSwitchToAsk, 
  onError 
}) => {
  // State Management
  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  const [filter, setFilter] = useState('');

  // Load data on mount and when context changes
  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (context.refreshData) {
      loadData();
    }
  }, [context]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load documents and collections in parallel
      const [docsData, collectionsData] = await Promise.all([
        apiClient.getDocuments(),
        apiClient.getCollections()
      ]);
      
      setDocuments(docsData.documents || {});
      setCollections(collectionsData.collections || []);
      
    } catch (err) {
      setError(err.message);
      onError?.(err);
    } finally {
      setLoading(false);
    }
  };

  // File Upload Handler
  const handleFileUpload = useCallback(async (files) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      try {
        // Update progress
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: { status: 'uploading', progress: 0 }
        }));

        // Upload file
        const result = await apiClient.uploadDocument(file, false);
        
        // Update progress based on result
        if (result.status === 'already_exists') {
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { 
              status: 'exists', 
              message: result.message,
              chunks: result.chunks_created 
            }
          }));
        } else if (result.status === 'success') {
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { 
              status: 'complete', 
              message: result.message,
              chunks: result.chunks_created 
            }
          }));
          
          // Refresh document list
          await loadData();
        } else {
          throw new Error(result.message || 'Upload failed');
        }

      } catch (err) {
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: { 
            status: 'error', 
            message: err.message 
          }
        }));
      }
    }

    // Clear progress after 5 seconds
    setTimeout(() => {
      setUploadProgress({});
    }, 5000);

  }, []);

  // Force Upload Handler
  const handleForceUpload = async (filename) => {
    try {
      // Note: In a real implementation, we'd need to store the original file
      // For now, show instruction to user
      alert('To force upload, please re-select the file and use the force option');
    } catch (err) {
      setError(err.message);
    }
  };

  // Document Actions
  const handleSearchDocument = (filename) => {
    onSwitchToSearch({
      preFilters: {
        documents: [filename]
      },
      placeholder: `Search in ${filename}...`
    });
  };

  const handleAskAboutDocument = (filename) => {
    onSwitchToAsk({
      preloadedContext: {
        documents: [filename]
      },
      placeholder: `Ask questions about ${filename}...`
    });
  };

  // Filter documents
  const filteredDocuments = Object.entries(documents).filter(([filename]) =>
    filename.toLowerCase().includes(filter.toLowerCase())
  );

  // Render document card
  const renderDocumentCard = (filename, data) => {
    const uploadStatus = uploadProgress[filename];
    
    return (
      <div key={filename} className="document-card">
        <div className="document-header">
          <div className="document-title">
            📄 {filename}
          </div>
          <div className="document-status">
            {uploadStatus ? (
              <span className={`status ${uploadStatus.status}`}>
                {uploadStatus.status === 'uploading' && '⏳ Uploading...'}
                {uploadStatus.status === 'complete' && '✅ Complete'}
                {uploadStatus.status === 'exists' && '📄 Already exists'}
                {uploadStatus.status === 'error' && '❌ Error'}
              </span>
            ) : (
              <span className="status ready">✅ Ready</span>
            )}
          </div>
        </div>

        <div className="document-info">
          <div className="document-stats">
            📊 {data.total_chunks} chunks total
          </div>
          
          <div className="document-collections">
            {Object.entries(data.collections).map(([collection, count]) => (
              <span key={collection} className="collection-tag">
                {collection}: {count}
              </span>
            ))}
          </div>
        </div>

        {uploadStatus?.message && (
          <div className={`upload-message ${uploadStatus.status}`}>
            {uploadStatus.message}
          </div>
        )}

        <div className="document-actions">
          <button 
            className="action-button search"
            onClick={() => handleSearchDocument(filename)}
          >
            🔍 Search This
          </button>
          <button 
            className="action-button ask"
            onClick={() => handleAskAboutDocument(filename)}
          >
            💬 Ask Questions
          </button>
          {uploadStatus?.status === 'exists' && (
            <button 
              className="action-button force"
              onClick={() => handleForceUpload(filename)}
            >
              🔄 Force Upload
            </button>
          )}
        </div>
      </div>
    );
  };

  // Drag and Drop Handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  if (loading) {
    return (
      <div className="browse-tab">
        <LoadingSpinner message="Loading documents..." />
      </div>
    );
  }

  return (
    <div className="browse-tab">
      {/* Header */}
      <div className="browse-header">
        <h2>📚 Document Library</h2>
        <div className="browse-stats">
          {Object.keys(documents).length} documents • {' '}
          {Object.values(documents).reduce((sum, doc) => sum + doc.total_chunks, 0)} chunks
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <ErrorDisplay 
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Upload Area */}
      <div 
        className="upload-area"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="upload-content">
          <div className="upload-icon">📤</div>
          <div className="upload-text">
            <strong>Drag & drop files here or click to browse</strong>
            <br />
            Supported: {config.allowedFileTypes.join(', ')} • 
            Max size: {config.getMaxFileSizeFormatted()}
          </div>
          <input
            type="file"
            multiple
            accept={config.allowedFileTypes.join(',')}
            onChange={(e) => handleFileUpload(e.target.files)}
            className="upload-input"
          />
        </div>
      </div>

      {/* Document Filter */}
      <div className="document-filter">
        <input
          type="text"
          placeholder="Filter documents..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-input"
        />
      </div>

      {/* Documents List */}
      <div className="documents-section">
        <h3>📄 Documents ({filteredDocuments.length})</h3>
        
        {filteredDocuments.length === 0 ? (
          <div className="empty-state">
            {Object.keys(documents).length === 0 
              ? 'No documents uploaded yet. Upload some files to get started!'
              : 'No documents match your filter.'
            }
          </div>
        ) : (
          <div className="documents-grid">
            {filteredDocuments.map(([filename, data]) => 
              renderDocumentCard(filename, data)
            )}
          </div>
        )}
      </div>

      {/* Collections Section */}
      <div className="collections-section">
        <h3>🗂️ Collections ({collections.length})</h3>
        
        <div className="collections-grid">
          {collections.map(collection => (
            <div key={collection.name} className="collection-card">
              <div className="collection-name">
                📚 {collection.name}
              </div>
              <div className="collection-count">
                {collection.item_count} items
              </div>
              {collection.unique_documents && (
                <div className="collection-documents">
                  Documents: {collection.unique_documents.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BrowseTab;