import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

// Apply persisted theme before React mounts to avoid flash
const persistedTheme = localStorage.getItem('knowa-theme') || 'autumn-light';
document.documentElement.dataset.theme = persistedTheme;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

