/**
 * Ask Tab Component
 * Conversational Q&A interface with source tracking
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '../../api/client.js';
import config from '../../api/config.js';
import LoadingSpinner from '../common/LoadingSpinner.js';
import ErrorDisplay from '../common/ErrorDisplay.js';
import './AskTab.css';

const AskTab = ({ 
  context, 
  onSwitchToSearch, 
  onSwitchToBrowse, 
  onError 
}) => {
  // State Management
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Context Configuration
  const [contextConfig, setContextConfig] = useState({
    strategy: 'enhanced',
    searchId: null,
    documents: [],
    chunkIds: []
  });

  // Available options
  const [availableDocuments, setAvailableDocuments] = useState([]);
  
  // Refs
  const conversationRef = useRef(null);

  // Load initial data and handle context
  useEffect(() => {
    loadAvailableDocuments();
  }, []);

  useEffect(() => {
    if (context.preloadedContext) {
      setContextConfig(prev => ({ ...prev, ...context.preloadedContext }));
    }
    if (context.suggestedQuestion) {
      setQuestion(context.suggestedQuestion);
    }
    if (context.autoAsk && context.suggestedQuestion) {
      // Auto-ask if requested
      setTimeout(() => handleAskQuestion(context.suggestedQuestion), 100);
    }
  }, [context]);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
    }
  }, [conversation]);

  const loadAvailableDocuments = async () => {
    try {
      const docsData = await apiClient.getDocuments();
      setAvailableDocuments(Object.keys(docsData.documents || {}));
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  // Ask Question Handler
  const handleAskQuestion = useCallback(async (questionText = question) => {
    if (!questionText.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Add question to conversation
      const questionEntry = {
        type: 'question',
        content: questionText,
        timestamp: new Date().toISOString()
      };
      
      setConversation(prev => [...prev, questionEntry]);

      // Build conversation history for API
      const conversationHistory = conversation
        .map(entry => `${entry.type === 'question' ? 'User' : 'Assistant'}: ${entry.content}`)
        .join('\n');

      // Build ask options
      const askOptions = {
        topK: config.defaultTopK,
        strategy: contextConfig.strategy,
        history: conversationHistory
      };

      // Add context based on configuration
      if (contextConfig.searchId) {
        askOptions.searchId = contextConfig.searchId;
      } else if (contextConfig.chunkIds.length > 0) {
        askOptions.chunkIds = contextConfig.chunkIds;
      } else if (contextConfig.documents.length > 0) {
        askOptions.documents = contextConfig.documents;
      }

      // Perform ask
      const response = await apiClient.ask(questionText, askOptions);
      
      // Add answer to conversation
      const answerEntry = {
        type: 'answer',
        content: response.answer,
        sources: response.sources || [],
        processingTime: response.processing_time,
        timestamp: new Date().toISOString()
      };
      
      setConversation(prev => [...prev, answerEntry]);
      setQuestion(''); // Clear input

    } catch (err) {
      setError(err.message);
      onError?.(err);
    } finally {
      setLoading(false);
    }
  }, [question, contextConfig, conversation, onError]);

  // Context Configuration Handlers
  const handleDocumentSelection = (selectedDocs) => {
    setContextConfig(prev => ({
      ...prev,
      documents: selectedDocs,
      searchId: null, // Clear search ID when selecting documents
      chunkIds: [] // Clear chunk IDs when selecting documents
    }));
  };

  const handleStrategyChange = (strategy) => {
    setContextConfig(prev => ({ ...prev, strategy }));
  };

  const clearContext = () => {
    setContextConfig({
      strategy: 'enhanced',
      searchId: null,
      documents: [],
      chunkIds: []
    });
  };

  const clearConversation = () => {
    setConversation([]);
  };

  // Source Actions
  const handleViewSources = (sources) => {
    const documentNames = [...new Set(sources.map(s => s.document))];
    onSwitchToBrowse({
      highlightDocuments: documentNames,
      showSources: sources
    });
  };

  const handleSearchMore = (questionText) => {
    onSwitchToSearch({
      preQuery: questionText,
      placeholder: `Search for more about: ${questionText}`
    });
  };

  // Render conversation entry
  const renderConversationEntry = (entry, index) => {
    if (entry.type === 'question') {
      return (
        <div key={index} className="conversation-entry question">
          <div className="entry-header">
            <span className="entry-icon">👤</span>
            <span className="entry-timestamp">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <div className="entry-content">
            {entry.content}
          </div>
        </div>
      );
    } else {
      return (
        <div key={index} className="conversation-entry answer">
          <div className="entry-header">
            <span className="entry-icon">🤖</span>
            <span className="entry-timestamp">
              {new Date(entry.timestamp).toLocaleTimeString()}
              {entry.processingTime && (
                <span className="processing-time">
                  ({entry.processingTime.toFixed(2)}s)
                </span>
              )}
            </span>
          </div>
          <div className="entry-content">
            {entry.content}
          </div>
          {entry.sources && entry.sources.length > 0 && (
            <div className="entry-sources">
              <h4>📚 Sources ({entry.sources.length}):</h4>
              <div className="sources-list">
                {entry.sources.map((source, sourceIndex) => (
                  <div key={sourceIndex} className="source-item">
                    📄 {source.document}
                    {source.page && ` (Page ${source.page})`}
                    {source.score && ` - ${Math.round(source.score * 100)}%`}
                  </div>
                ))}
              </div>
              <div className="sources-actions">
                <button 
                  className="action-button view"
                  onClick={() => handleViewSources(entry.sources)}
                >
                  📖 View Sources
                </button>
                <button 
                  className="action-button search"
                  onClick={() => handleSearchMore(entry.content)}
                >
                  🔍 Search More
                </button>
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  // Render context configuration
  const renderContextConfig = () => (
    <div className="context-config">
      <h3>🎛️ Context Configuration</h3>
      
      <div className="config-row">
        <div className="config-group">
          <label>📁 Limit to Documents:</label>
          <select 
            multiple
            value={contextConfig.documents}
            onChange={(e) => handleDocumentSelection(Array.from(e.target.selectedOptions, option => option.value))}
            className="config-select"
          >
            <option value="">All Documents</option>
            {availableDocuments.map(doc => (
              <option key={doc} value={doc}>{doc}</option>
            ))}
          </select>
        </div>
        
        <div className="config-group">
          <label>🧠 Strategy:</label>
          <select 
            value={contextConfig.strategy}
            onChange={(e) => handleStrategyChange(e.target.value)}
            className="config-select"
          >
            <option value="enhanced">Enhanced</option>
            <option value="basic">Basic</option>
            <option value="paragraph">Paragraph</option>
          </select>
        </div>
      </div>

      {/* Context Status */}
      <div className="context-status">
        {contextConfig.searchId && (
          <span className="context-tag">🔍 Using Search Results</span>
        )}
        {contextConfig.documents.length > 0 && (
          <span className="context-tag">
            📁 Limited to: {contextConfig.documents.join(', ')}
          </span>
        )}
        {contextConfig.chunkIds.length > 0 && (
          <span className="context-tag">
            🎯 Specific chunks: {contextConfig.chunkIds.length}
          </span>
        )}
        
        {(contextConfig.searchId || contextConfig.documents.length > 0 || contextConfig.chunkIds.length > 0) && (
          <button 
            className="clear-context-button"
            onClick={clearContext}
          >
            ❌ Clear Context
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="ask-tab">
      {/* Ask Header */}
      <div className="ask-header">
        <h2>💬 Ask Questions</h2>
        {conversation.length > 0 && (
          <button 
            className="clear-conversation-button"
            onClick={clearConversation}
          >
            🗑️ Clear Conversation
          </button>
        )}
      </div>

      {/* Context Configuration */}
      {renderContextConfig()}

      {/* Error Display */}
      {error && (
        <ErrorDisplay 
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Question Input */}
      <div className="question-input-section">
        <div className="question-input-container">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAskQuestion();
              }
            }}
            placeholder={context.placeholder || "Ask a question about your documents..."}
            className="question-input"
            rows="3"
          />
          <button 
            onClick={() => handleAskQuestion()}
            disabled={loading || !question.trim()}
            className="ask-button"
          >
            {loading ? '⏳' : '📤'}
          </button>
        </div>
      </div>

      {/* Conversation */}
      <div className="conversation-section">
        <div 
          ref={conversationRef}
          className="conversation-container"
        >
          {conversation.length === 0 ? (
            <div className="conversation-empty">
              <div className="empty-icon">💭</div>
              <div className="empty-text">
                Start a conversation by asking a question above.
                <br />
                You can ask about specific documents or search across your entire library.
              </div>
            </div>
          ) : (
            conversation.map((entry, index) => renderConversationEntry(entry, index))
          )}
          
          {loading && (
            <div className="conversation-entry loading">
              <LoadingSpinner message="Thinking..." />
            </div>
          )}
        </div>
      </div>

      {/* Suggested Questions */}
      {conversation.length === 0 && (
        <div className="suggested-questions">
          <h4>💡 Suggested Questions:</h4>
          <div className="suggestions-list">
            <button 
              className="suggestion-button"
              onClick={() => setQuestion("What are the main topics covered in my documents?")}
            >
              What are the main topics covered in my documents?
            </button>
            <button 
              className="suggestion-button"
              onClick={() => setQuestion("What is our company's policy on remote work?")}
            >
              What is our company's policy on remote work?
            </button>
            <button 
              className="suggestion-button"
              onClick={() => setQuestion("What are the security requirements?")}
            >
              What are the security requirements?
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AskTab;