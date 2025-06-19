/**
 * Status Tab Component
 * System health monitoring and statistics
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '../../api/client.js';
import config from '../../api/config.js';
import LoadingSpinner from '../common/LoadingSpinner.js';
import ErrorDisplay from '../common/ErrorDisplay.js';
import './StatusTab.css';

const StatusTab = ({ 
  context, 
  onSwitchToBrowse, 
  onError 
}) => {
  // State Management
  const [systemStatus, setSystemStatus] = useState(null);
  const [documentStats, setDocumentStats] = useState(null);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Health check interval
  const healthCheckInterval = useRef(null);

  // Load status on mount
  useEffect(() => {
    checkSystemStatus();
    
    if (autoRefresh) {
      startHealthCheck();
    }
    
    return () => {
      if (healthCheckInterval.current) {
        clearInterval(healthCheckInterval.current);
      }
    };
  }, [autoRefresh]);

  const startHealthCheck = () => {
    if (healthCheckInterval.current) {
      clearInterval(healthCheckInterval.current);
    }
    
    healthCheckInterval.current = setInterval(() => {
      checkSystemStatus(true); // Silent refresh
    }, config.pollingInterval);
  };

  const checkSystemStatus = useCallback(async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      
      // Perform health checks in parallel
      const [status, docs, collectionsData] = await Promise.all([
        apiClient.getStatus(),
        apiClient.getDocuments(),
        apiClient.getCollections()
      ]);
      
      setSystemStatus(status);
      setDocumentStats(docs);
      setCollections(collectionsData.collections || []);
      setLastChecked(new Date());
      
    } catch (err) {
      if (!silent) {
        setError(err.message);
        onError?.(err);
      }
      console.error('Health check failed:', err);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, [onError]);

  // Clear all data
  const handleClearAllData = async () => {
    const confirmed = window.confirm(
      'This will delete ALL documents and data. This action cannot be undone. Continue?'
    );
    
    if (!confirmed) return;

    try {
      setLoading(true);
      await apiClient.clearDocuments();
      
      // Refresh status
      await checkSystemStatus();
      
      alert('All data cleared successfully');
      
      // Switch to browse tab to show empty state
      onSwitchToBrowse({ refreshData: true });
      
    } catch (err) {
      setError(`Failed to clear data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Export data (placeholder for future implementation)
  const handleExportData = () => {
    alert('Export functionality coming soon!');
  };

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setAutoRefresh(prev => !prev);
  };

  // Render service status
  const renderServiceStatus = (service, status) => {
    const isHealthy = status === 'connected';
    
    return (
      <div key={service} className={`service-status ${isHealthy ? 'healthy' : 'unhealthy'}`}>
        <div className="service-icon">
          {isHealthy ? '✅' : '❌'}
        </div>
        <div className="service-info">
          <div className="service-name">
            {service.charAt(0).toUpperCase() + service.slice(1)}
          </div>
          <div className="service-state">
            {isHealthy ? 'Connected' : status}
          </div>
        </div>
      </div>
    );
  };

  // Render collection info
  const renderCollectionInfo = (collection) => (
    <div key={collection.name} className="collection-info">
      <div className="collection-header">
        <span className="collection-name">📚 {collection.name}</span>
        <span className="collection-count">{collection.item_count} items</span>
      </div>
      {collection.unique_documents && collection.unique_documents.length > 0 && (
        <div className="collection-documents">
          Documents: {collection.unique_documents.slice(0, 3).join(', ')}
          {collection.unique_documents.length > 3 && ` (+${collection.unique_documents.length - 3} more)`}
        </div>
      )}
      {collection.error && (
        <div className="collection-error">
          ⚠️ {collection.error}
        </div>
      )}
    </div>
  );

  if (loading && !systemStatus) {
    return (
      <div className="status-tab">
        <LoadingSpinner message="Checking system status..." />
      </div>
    );
  }

  return (
    <div className="status-tab">
      {/* Status Header */}
      <div className="status-header">
        <h2>⚙️ System Status</h2>
        <div className="status-controls">
          <button 
            className="refresh-button"
            onClick={() => checkSystemStatus()}
            disabled={loading}
          >
            🔄 Refresh
          </button>
          <button 
            className={`auto-refresh-button ${autoRefresh ? 'active' : ''}`}
            onClick={toggleAutoRefresh}
          >
            {autoRefresh ? '⏸️' : '▶️'} Auto-refresh
          </button>
        </div>
      </div>

      {/* Last Checked */}
      {lastChecked && (
        <div className="last-checked">
          Last checked: {lastChecked.toLocaleString()}
          {autoRefresh && ` (auto-refreshing every ${config.pollingInterval / 1000}s)`}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <ErrorDisplay 
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* API Configuration */}
      <div className="status-section">
        <h3>🌐 API Configuration</h3>
        <div className="config-info">
          <div className="config-item">
            <strong>Base URL:</strong> {config.apiBaseUrl}
          </div>
          <div className="config-item">
            <strong>Environment:</strong> {config.isDevelopment ? 'Development' : 'Production'}
          </div>
          <div className="config-item">
            <strong>Timeout:</strong> {config.apiTimeout / 1000}s
          </div>
          <div className="config-item">
            <strong>Debug Mode:</strong> {config.debugMode ? 'Enabled' : 'Disabled'}
          </div>
        </div>
      </div>

      {/* Service Health */}
      <div className="status-section">
        <h3>🔧 Service Health</h3>
        {systemStatus ? (
          <div className="services-grid">
            {Object.entries(systemStatus).map(([service, status]) => 
              renderServiceStatus(service, status)
            )}
          </div>
        ) : (
          <div className="no-data">No service status available</div>
        )}
      </div>

      {/* Document Statistics */}
      <div className="status-section">
        <h3>📊 Document Statistics</h3>
        {documentStats ? (
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{Object.keys(documentStats.documents || {}).length}</div>
              <div className="stat-label">📄 Documents</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{documentStats.total_items || 0}</div>
              <div className="stat-label">🧩 Total Chunks</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{collections.length}</div>
              <div className="stat-label">🗂️ Collections</div>
            </div>
          </div>
        ) : (
          <div className="no-data">No document statistics available</div>
        )}
      </div>

      {/* Collections Detail */}
      <div className="status-section">
        <h3>🗂️ Collections Detail</h3>
        {collections.length > 0 ? (
          <div className="collections-list">
            {collections.map(collection => renderCollectionInfo(collection))}
          </div>
        ) : (
          <div className="no-data">No collections found</div>
        )}
      </div>

      {/* File Upload Configuration */}
      <div className="status-section">
        <h3>📤 Upload Configuration</h3>
        <div className="config-info">
          <div className="config-item">
            <strong>Max File Size:</strong> {config.getMaxFileSizeFormatted()}
          </div>
          <div className="config-item">
            <strong>Allowed Types:</strong> {config.allowedFileTypes.join(', ')}
          </div>
          <div className="config-item">
            <strong>Default Top-K:</strong> {config.defaultTopK}
          </div>
          <div className="config-item">
            <strong>Default Confidence:</strong> {Math.round(config.defaultConfidenceThreshold * 100)}%
          </div>
        </div>
      </div>

      {/* System Actions */}
      <div className="status-section">
        <h3>🛠️ System Actions</h3>
        <div className="actions-grid">
          <button 
            className="action-button danger"
            onClick={handleClearAllData}
            disabled={loading}
          >
            🧹 Clear All Data
          </button>
          <button 
            className="action-button"
            onClick={handleExportData}
            disabled={loading}
          >
            📥 Export Data
          </button>
          <button 
            className="action-button"
            onClick={() => onSwitchToBrowse({ refreshData: true })}
          >
            📚 View Documents
          </button>
        </div>
        
        <div className="action-warning">
          ⚠️ Clear All Data will permanently delete all uploaded documents and cannot be undone.
        </div>
      </div>
    </div>
  );
};

export default StatusTab;