/**
 * Tab Navigation Component
 * Provides clean tab interface with active state management
 */

import React from 'react';
import './TabNavigation.css';

const TabNavigation = ({ tabs, activeTab, onTabChange }) => {
  return (
    <nav className="tab-navigation">
      <div className="tab-list">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
            title={tab.description}
          >
            <span className="tab-label">{tab.label}</span>
            <span className="tab-description">{tab.description}</span>
          </button>
        ))}
      </div>
      
      {/* Tab Indicator */}
      <div 
        className="tab-indicator"
        style={{
          transform: `translateX(${tabs.findIndex(tab => tab.id === activeTab) * 100}%)`
        }}
      />
    </nav>
  );
};

export default TabNavigation;