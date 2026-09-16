import React from 'react';
import { NavLink } from 'react-router-dom';
import { Bell, BarChart3, BellRing, BriefcaseBusiness, ChartNoAxesCombined, ClipboardList, FileText, FolderKanban, Gauge, Settings, UserRound } from 'lucide-react';

const main=[['Overview','/officer/overview',Gauge],['Projects','/officer/projects',FolderKanban],['Attention Queue','/officer/attention',BellRing],['Alerts','/officer/alerts',Bell],['Reviews','/officer/reviews',ClipboardList],['Monitoring','/officer/monitoring',ChartNoAxesCombined],['Analytics','/officer/analytics',BarChart3],['Reports','/officer/reports',FileText]];
const second=[['My Workspace','/officer/workspace',BriefcaseBusiness],['Notifications','/officer/notifications',Bell],['Settings','/officer/settings',Settings]];
const Nav=({items})=><div className="nav-group">{items.map(([label,to,Icon])=><NavLink key={to} className="nav-link" to={to}><Icon/><span>{label}</span>{label==='Alerts'&&<b className="badge pill red">3</b>}</NavLink>)}</div>;
export default function OfficerSidebar(){return <aside className="officer-sidebar"><Nav items={main}/><div className="nav-divider"/><Nav items={second}/><div className="sidebar-art">Nationwide Project Intelligence<br/>for a Developed India</div></aside>}
