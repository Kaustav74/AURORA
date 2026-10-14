import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuroraProvider } from './context/AuroraContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuroraProvider>
      <App />
    </AuroraProvider>
  </React.StrictMode>
);
