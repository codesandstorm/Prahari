import React from 'react';
import { Outlet } from 'react-router-dom';
import OfficerHeader from './OfficerHeader';
import OfficerSidebar from './OfficerSidebar';
import { AskPrahariDrawer, AskPrahariLauncher, AskPrahariProvider } from '../assistant/AskPrahari';
import { useDemoStore } from '../../state/DemoStore';

export default function OfficerLayout(){const {settings}=useDemoStore();return <AskPrahariProvider><div className={`app-shell density-${settings.density}`}><OfficerHeader/><div className="app-body"><OfficerSidebar/><main><Outlet/></main></div><AskPrahariLauncher/><AskPrahariDrawer/></div></AskPrahariProvider>}
