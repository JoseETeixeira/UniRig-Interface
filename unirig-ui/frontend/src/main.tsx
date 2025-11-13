import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

/**
 * Application entry point
 */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Enable React DevTools in development
if (typeof import.meta !== 'undefined' && 'env' in import.meta && (import.meta as any).env?.DEV) {
  // React DevTools will automatically connect when available
  console.log('🔧 React DevTools enabled');
}
