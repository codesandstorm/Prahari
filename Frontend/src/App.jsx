import React, { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import PortalHeader from './components/layout/PortalHeader';
import PortalFooter from './components/layout/PortalFooter';
import PaimanaHome from './pages/paimana/PaimanaHome';
import OfficerDashboard from './pages/prahari/OfficerDashboard';
import { AnalyticsPage, AssistantPage, DataTrustPage, ModelValidationPage, ProjectIntelligencePage, ReviewQueuePage, SandboxPage } from './pages/prahari/PrahariPages';

export default function App() { const location = useLocation(); const prahariActive = location.pathname.startsWith('/prahari'); const isPaimanaHome = location.pathname === '/'; useEffect(() => { document.body.classList.toggle('prahari-active', prahariActive); }, [prahariActive]); return <>{!isPaimanaHome && <PortalHeader />}<Routes><Route path="/" element={<PaimanaHome />} /><Route path="/prahari" element={<OfficerDashboard />} /><Route path="/prahari/review-queue" element={<ReviewQueuePage />} /><Route path="/prahari/project/:id" element={<ProjectIntelligencePage />} /><Route path="/prahari/analytics" element={<AnalyticsPage />} /><Route path="/prahari/data-trust" element={<DataTrustPage />} /><Route path="/prahari/model-validation" element={<ModelValidationPage />} /><Route path="/prahari/cuf-sandbox" element={<SandboxPage />} /><Route path="/prahari/assistant" element={<AssistantPage />} /><Route path="*" element={<Navigate to="/prahari" replace />} /></Routes>{!isPaimanaHome && <PortalFooter />}</>; }
