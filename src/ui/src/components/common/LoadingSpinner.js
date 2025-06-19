/**
 * Loading Spinner Component
 * Reusable loading indicator with optional message
 */

import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Loading...', size = 'medium' }) => {
  return (
    <div className={`loading-spinner ${size}`}>
      <div className="spinner-icon">⏳</div>
      <div className="spinner-message">{message}</div>
    </div>
  );
};

export default LoadingSpinner;