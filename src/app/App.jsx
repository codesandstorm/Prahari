import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import OfficerLayout from '../components/layout/OfficerLayout';
import LoginPage from '../pages/auth/LoginPage';
import OverviewPage from '../pages/officer/OverviewPage';
import { AnalyticsPage, AttentionPage, MonitoringPage, NotificationsPage, ProjectsPage, ReportsPage, SettingsPage, WorkspacePage } from '../pages/officer/PortfolioPages';
import { AlertDetailsPage, AlertsPage, ReviewDetailsPage, ReviewsPage } from '../pages/officer/WorkflowPages';
import { CostPage, ExecutionHealthPage, MilestonesPage, ProjectOverviewPage, SchedulePage } from '../pages/project/ProjectPages';
import LandingPage from '../pages/public/LandingPage';

export default function App(){return <Routes>
  <Route path="/" element={<LandingPage/>}/>
  <Route path="/login" element={<LoginPage/>}/>
  <Route path="/officer" element={<OfficerLayout/>}>
    <Route index element={<Navigate to="overview" replace/>}/>
    <Route path="overview" element={<OverviewPage/>}/>
    <Route path="projects" element={<ProjectsPage/>}/>
    <Route path="attention" element={<AttentionPage/>}/>
    <Route path="alerts" element={<AlertsPage/>}/>
    <Route path="alerts/:alertId" element={<AlertDetailsPage/>}/>
    <Route path="reviews" element={<ReviewsPage/>}/>
    <Route path="reviews/:reviewId" element={<ReviewDetailsPage/>}/>
    <Route path="monitoring" element={<MonitoringPage/>}/>
    <Route path="analytics" element={<AnalyticsPage/>}/>
    <Route path="reports" element={<ReportsPage/>}/>
    <Route path="workspace" element={<WorkspacePage/>}/>
    <Route path="notifications" element={<NotificationsPage/>}/>
    <Route path="settings" element={<SettingsPage/>}/>
    <Route path="projects/:projectId" element={<ProjectOverviewPage/>}/>
    <Route path="projects/:projectId/schedule" element={<SchedulePage/>}/>
    <Route path="projects/:projectId/cost" element={<CostPage/>}/>
    <Route path="projects/:projectId/execution-health" element={<ExecutionHealthPage/>}/>
    <Route path="projects/:projectId/milestones" element={<MilestonesPage/>}/>
  </Route>
  <Route path="*" element={<Navigate to="/" replace/>}/>
</Routes>}
