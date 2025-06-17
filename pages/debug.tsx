import { useState, useEffect } from 'react';

export default function DebugPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [apiStatus, setApiStatus] = useState<string>('unknown');

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testConnection = async () => {
    addLog('Starting connection test...');
    
    try {
      // Test with window.location.hostname
      const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
      const apiUrl = `http://${hostname}:8000/status`;
      
      addLog(`Attempting to connect to: ${apiUrl}`);
      
      const response = await fetch(apiUrl);
      
      if (response.ok) {
        const data = await response.json();
        addLog(`✅ Connection successful! Status: ${response.status}`);
        addLog(`Response: ${JSON.stringify(data)}`);
        setApiStatus('connected');
      } else {
        addLog(`❌ Connection failed with status: ${response.status}`);
        setApiStatus('failed');
      }
    } catch (error) {
      addLog(`❌ Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setApiStatus('error');
    }
  };

  useEffect(() => {
    addLog('Debug page loaded');
    addLog(`Window hostname: ${typeof window !== 'undefined' ? window.location.hostname : 'not available'}`);
    addLog(`Window location: ${typeof window !== 'undefined' ? window.location.href : 'not available'}`);
    
    // Auto-test connection
    testConnection();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>RAG UI Debug Page</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>API Status: <span style={{ color: apiStatus === 'connected' ? 'green' : 'red' }}>{apiStatus}</span></h2>
        <button onClick={testConnection} style={{ padding: '10px', margin: '10px 0' }}>
          Test Connection Again
        </button>
      </div>

      <div style={{ backgroundColor: '#f5f5f5', padding: '15px', borderRadius: '5px' }}>
        <h3>Connection Logs:</h3>
        <div style={{ maxHeight: '400px', overflow: 'auto' }}>
          {logs.map((log, index) => (
            <div key={index} style={{ margin: '5px 0' }}>
              {log}
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Quick Actions:</h3>
        <button onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
          Open API Docs
        </button>
        <button onClick={() => window.open('http://localhost:8000/status', '_blank')} style={{ marginLeft: '10px' }}>
          Test API Status
        </button>
      </div>
    </div>
  );
}