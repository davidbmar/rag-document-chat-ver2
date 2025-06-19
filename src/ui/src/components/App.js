/**
 * Main RAG UI Application Component
 * Manages tab navigation and inter-tab context passing
 */

import React, { useState, useEffect } from 'react';
import './App.css';

// Tab Components
import SearchTab from './tabs/SearchTab.js';
import AskTab from './tabs/AskTab.js';
import BrowseTab from './tabs/BrowseTab.js';
import StatusTab from './tabs/StatusTab.js';

// Common Components
import TabNavigation from './common/TabNavigation.js';
import ErrorDisplay from './common/ErrorDisplay.js';

// API Client
import apiClient from '../api/client.js';
import config from '../api/config.js';

const App = () => {
  // Tab State Management
  const [activeTab, setActiveTab] = useState('browse');
  const [tabContexts, setTabContexts] = useState({
    search: {},
    ask: {},
    browse: {},
    status: {}
  });

  // Global State
  const [systemHealth, setSystemHealth] = useState(null);
  const [globalError, setGlobalError] = useState(null);

  // Initialize app
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check system health on startup
      const health = await apiClient.healthCheck();
      setSystemHealth(health);
      
      if (!health.healthy) {
        setGlobalError(`System unhealthy: ${health.error}`);
      }
    } catch (error) {
      setGlobalError(`Failed to connect to API: ${error.message}`);
    }
  };

  // Tab Navigation with Context
  const switchToTab = (tabName, context = {}) => {
    setTabContexts(prev => ({
      ...prev,
      [tabName]: { ...prev[tabName], ...context }
    }));
    setActiveTab(tabName);
  };

  const switchToSearch = (context = {}) => switchToTab('search', context);
  const switchToAsk = (context = {}) => switchToTab('ask', context);
  const switchToBrowse = (context = {}) => switchToTab('browse', context);
  const switchToStatus = (context = {}) => switchToTab('status', context);

  // Error Handling
  const handleGlobalError = (error) => {
    console.error('Global error:', error);
    setGlobalError(error.message || error);
  };

  const clearGlobalError = () => {
    setGlobalError(null);
  };

  // Tab Definitions
  const tabs = [
    {
      id: 'search',
      label: '🔍 Search',
      description: 'Find information across documents',
      component: SearchTab
    },
    {
      id: 'ask',
      label: '💬 Ask',
      description: 'Get answers to your questions',
      component: AskTab
    },
    {
      id: 'browse',
      label: '📚 Browse', 
      description: 'Manage documents and collections',
      component: BrowseTab
    },
    {
      id: 'status',
      label: '⚙️ Status',
      description: 'System health and statistics',
      component: StatusTab
    }
  ];

  // Render Current Tab
  const renderCurrentTab = () => {
    const currentTab = tabs.find(tab => tab.id === activeTab);
    if (!currentTab) return <div>Tab not found</div>;

    const TabComponent = currentTab.component;
    const context = tabContexts[activeTab];

    return (
      <TabComponent
        context={context}
        onSwitchToSearch={switchToSearch}
        onSwitchToAsk={switchToAsk}
        onSwitchToBrowse={switchToBrowse}
        onSwitchToStatus={switchToStatus}
        onError={handleGlobalError}
      />
    );
  };

  return (
    <div className="rag-app">
      {/* Header */}
      <header className="app-header">
        <div className="app-title">
          <h1>📚 RAG Document Chat</h1>
          <span className="app-subtitle">
            Environment: {config.isDevelopment ? 'Development' : 'Production'}
          </span>
        </div>
        
        {/* System Health Indicator */}
        {systemHealth && (
          <div className={`health-indicator ${systemHealth.healthy ? 'healthy' : 'unhealthy'}`}>
            {systemHealth.healthy ? '✅ Connected' : '❌ Disconnected'}
          </div>
        )}
      </header>

      {/* Global Error Display */}
      {globalError && (
        <ErrorDisplay 
          error={globalError}
          onDismiss={clearGlobalError}
          type="global"
        />
      )}

      {/* Tab Navigation */}
      <TabNavigation
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Tab Content */}
      <main className="tab-content">
        {renderCurrentTab()}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-info">
          API: {config.apiBaseUrl} | 
          Max File Size: {config.getMaxFileSizeFormatted()} |
          Allowed Types: {config.allowedFileTypes.join(', ')}
        </div>
      </footer>
    </div>
  );
};

export default App;