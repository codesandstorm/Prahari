import React from 'react';
import { NavLink } from 'react-router-dom';
import { Bell, BarChart3, BellRing, BriefcaseBusiness, ChartNoAxesCombined, ClipboardList, FileText, FolderKanban, Gauge, Settings, UserRound } from 'lucide-react';
import { useDemoStore } from '../../state/DemoStore';

const main=[['Overview','/officer/overview',Gauge],['Projects','/officer/projects',FolderKanban],['Attention Queue','/officer/attention',BellRing],['Alerts','/officer/alerts',Bell],['Reviews','/officer/reviews',ClipboardList],['Monitoring','/officer/monitoring',ChartNoAxesCombined],['Analytics','/officer/analytics',BarChart3],['Reports','/officer/reports',FileText]];
const second=[['My Workspace','/officer/workspace',BriefcaseBusiness],['Notifications','/officer/notifications',Bell],['Settings','/officer/settings',Settings]];
const Nav=({items,badges})=><div className="nav-group">{items.map(([label,to,Icon])=><NavLink key={to} className="nav-link" to={to}><Icon/><span>{label}</span>{badges[label]>0&&<b className="badge pill red">{badges[label]}</b>}</NavLink>)}</div>;
export default function OfficerSidebar(){const {activeAlertCount,unreadCount}=useDemoStore();const badges={Alerts:activeAlertCount,Notifications:unreadCount};return <aside className="officer-sidebar"><Nav items={main} badges={badges}/><div className="nav-divider"/><Nav items={second} badges={badges}/><div className="sidebar-art">Nationwide Project Intelligence<br/>for a Developed India</div></aside>}
