/**
 * Error Display Component
 * Reusable error message display with dismiss functionality
 */

import React from 'react';
import './ErrorDisplay.css';

const ErrorDisplay = ({ error, onDismiss, type = 'default' }) => {
  return (
    <div className={`error-display ${type}`}>
      <div className="error-content">
        <div className="error-icon">❌</div>
        <div className="error-message">
          {typeof error === 'string' ? error : error.message || 'An error occurred'}
        </div>
        {onDismiss && (
          <button 
            className="error-dismiss"
            onClick={onDismiss}
            title="Dismiss error"
          >
            ✕
          </button>
        )}
      </div>
      
      {type === 'global' && (
        <div className="error-details">
          Check your network connection and ensure the API server is running.
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;