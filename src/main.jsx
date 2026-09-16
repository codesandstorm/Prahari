import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './app/App';
import { DemoStoreProvider } from './state/DemoStore';
import './styles/tokens.css';
import './styles/globals.css';
import './styles/components.css';
import './styles/extended.css';
import './styles/workspace.css';
import './styles/responsive.css';
import './styles/assistant.css';
import './styles/hardening.css';

createRoot(document.getElementById('root')).render(<React.StrictMode><BrowserRouter><DemoStoreProvider><App /></DemoStoreProvider></BrowserRouter></React.StrictMode>);
