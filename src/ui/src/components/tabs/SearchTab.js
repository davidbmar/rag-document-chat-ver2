/**
 * Search Tab Component
 * Document search interface with filtering and results display
 */

import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '../../api/client.js';
import config from '../../api/config.js';
import LoadingSpinner from '../common/LoadingSpinner.js';
import ErrorDisplay from '../common/ErrorDisplay.js';
import './SearchTab.css';

const SearchTab = ({ 
  context, 
  onSwitchToAsk, 
  onSwitchToBrowse, 
  onError 
}) => {
  // State Management
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searchMetadata, setSearchMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Filter State
  const [filters, setFilters] = useState({
    documents: [],
    collections: ['documents'], // Default to documents collection
    threshold: config.defaultConfidenceThreshold,
    topK: config.defaultTopK
  });
  
  // Available options for filters
  const [availableDocuments, setAvailableDocuments] = useState([]);
  const [availableCollections, setAvailableCollections] = useState([]);

  // Load initial data and handle context
  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    if (context.preFilters) {
      setFilters(prev => ({ ...prev, ...context.preFilters }));
    }
    if (context.preQuery) {
      setQuery(context.preQuery);
      handleSearch(context.preQuery);
    }
    if (context.placeholder) {
      // Could be used to update input placeholder
    }
  }, [context]);

  const loadFilterOptions = async () => {
    try {
      const [docsData, collectionsData] = await Promise.all([
        apiClient.getDocuments(),
        apiClient.getCollections()
      ]);
      
      setAvailableDocuments(Object.keys(docsData.documents || {}));
      setAvailableCollections(collectionsData.collections?.map(c => c.name) || []);
      
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  // Search Handler
  const handleSearch = useCallback(async (searchQuery = query) => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Build search options
      const searchOptions = {
        topK: filters.topK,
        filters: {
          threshold: filters.threshold
        }
      };

      // Add collection filters
      if (filters.collections.length > 0) {
        searchOptions.filters.collections = filters.collections;
      }

      // Add document filters
      if (filters.documents.length > 0) {
        searchOptions.filters.documents = filters.documents;
      }

      // Perform search
      const searchResults = await apiClient.search(searchQuery, searchOptions);
      
      setResults(searchResults.results || []);
      setSearchMetadata({
        searchId: searchResults.search_id,
        totalResults: searchResults.total_results,
        processingTime: searchResults.processing_time,
        collectionsSearched: searchResults.collections_searched,
        uniqueDocuments: searchResults.unique_documents
      });

    } catch (err) {
      setError(err.message);
      onError?.(err);
    } finally {
      setLoading(false);
    }
  }, [query, filters, onError]);

  // Result Actions
  const handleAskAboutResult = (result) => {
    onSwitchToAsk({
      preloadedContext: {
        chunkIds: [result.chunk_id]
      },
      suggestedQuestion: `Tell me more about: "${result.content.substring(0, 50)}..."`
    });
  };

  const handleAskAboutAllResults = () => {
    if (searchMetadata?.searchId) {
      onSwitchToAsk({
        preloadedContext: {
          searchId: searchMetadata.searchId
        },
        suggestedQuestion: `What can you tell me about "${query}"?`
      });
    }
  };

  const handleViewDocument = (documentName) => {
    onSwitchToBrowse({
      highlightDocument: documentName,
      scrollToDocument: documentName
    });
  };

  // Filter Handlers
  const handleDocumentFilterChange = (selectedDocs) => {
    setFilters(prev => ({ ...prev, documents: selectedDocs }));
  };

  const handleCollectionFilterChange = (selectedCollections) => {
    setFilters(prev => ({ ...prev, collections: selectedCollections }));
  };

  // Render search result
  const renderSearchResult = (result, index) => {
    const confidence = Math.round(result.score * 100);
    const confidenceBar = '█'.repeat(Math.max(1, Math.floor(result.score * 10)));
    
    return (
      <div key={result.chunk_id || index} className="search-result">
        <div className="result-header">
          <div className="result-document">
            📄 {result.document}
          </div>
          <div className="result-confidence">
            <span className="confidence-score">{confidence}%</span>
            <span className="confidence-bar">{confidenceBar}</span>
          </div>
        </div>
        
        <div className="result-metadata">
          Collection: {result.collection} | Chunk: {result.chunk_id}
        </div>
        
        <div className="result-content">
          {result.content}
        </div>
        
        <div className="result-actions">
          <button 
            className="action-button ask"
            onClick={() => handleAskAboutResult(result)}
          >
            💬 Ask About This
          </button>
          <button 
            className="action-button view"
            onClick={() => handleViewDocument(result.document)}
          >
            📖 View Document
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="search-tab">
      {/* Search Header */}
      <div className="search-header">
        <h2>🔍 Search Documents</h2>
      </div>

      {/* Search Input */}
      <div className="search-input-section">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={context.placeholder || "Search across all documents..."}
            className="search-input"
          />
          <button 
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
            className="search-button"
          >
            {loading ? '⏳' : '🔎'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="search-filters">
        <h3>🎛️ Filters</h3>
        
        <div className="filter-row">
          <div className="filter-group">
            <label>📁 Documents:</label>
            <select 
              multiple
              value={filters.documents}
              onChange={(e) => handleDocumentFilterChange(Array.from(e.target.selectedOptions, option => option.value))}
              className="filter-select"
            >
              <option value="">All Documents</option>
              {availableDocuments.map(doc => (
                <option key={doc} value={doc}>{doc}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>🗂️ Collections:</label>
            <select 
              multiple
              value={filters.collections}
              onChange={(e) => handleCollectionFilterChange(Array.from(e.target.selectedOptions, option => option.value))}
              className="filter-select"
            >
              {availableCollections.map(collection => (
                <option key={collection} value={collection}>{collection}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="filter-row">
          <div className="filter-group">
            <label>🎯 Min Confidence: {Math.round(filters.threshold * 100)}%</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={filters.threshold}
              onChange={(e) => setFilters(prev => ({ ...prev, threshold: parseFloat(e.target.value) }))}
              className="filter-range"
            />
          </div>
          
          <div className="filter-group">
            <label>📊 Max Results:</label>
            <select 
              value={filters.topK}
              onChange={(e) => setFilters(prev => ({ ...prev, topK: parseInt(e.target.value) }))}
              className="filter-select"
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="15">15</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <ErrorDisplay 
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Loading */}
      {loading && (
        <LoadingSpinner message="Searching documents..." />
      )}

      {/* Search Results */}
      {searchMetadata && !loading && (
        <div className="search-results">
          <div className="results-header">
            <h3>📋 Results ({searchMetadata.totalResults} found in {searchMetadata.processingTime?.toFixed(2)}s)</h3>
            
            <div className="results-metadata">
              <div>Search ID: {searchMetadata.searchId}</div>
              <div>Collections: {searchMetadata.collectionsSearched?.join(', ')}</div>
              <div>Documents: {searchMetadata.uniqueDocuments?.join(', ')}</div>
            </div>
            
            {results.length > 0 && (
              <div className="results-actions">
                <button 
                  className="action-button ask-all"
                  onClick={handleAskAboutAllResults}
                >
                  💬 Ask Questions About All Results
                </button>
              </div>
            )}
          </div>

          {results.length === 0 ? (
            <div className="no-results">
              No results found for "{query}". Try adjusting your filters or search terms.
            </div>
          ) : (
            <div className="results-list">
              {results.map((result, index) => renderSearchResult(result, index))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchTab;