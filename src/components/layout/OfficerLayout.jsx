import React from 'react';
import { Outlet } from 'react-router-dom';
import OfficerHeader from './OfficerHeader';
import OfficerSidebar from './OfficerSidebar';
import { AskPrahariDrawer, AskPrahariLauncher, AskPrahariProvider } from '../assistant/AskPrahari';

export default function OfficerLayout(){return <AskPrahariProvider><div className="app-shell"><OfficerHeader/><div className="app-body"><OfficerSidebar/><main><Outlet/></main></div><AskPrahariLauncher/><AskPrahariDrawer/></div></AskPrahariProvider>}
