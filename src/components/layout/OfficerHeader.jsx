import React from 'react';
import { CalendarDays } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useDemoStore } from '../../state/DemoStore';

export default function OfficerHeader(){const {logout}=useDemoStore();const navigate=useNavigate();return <header className="officer-header"><a className="brand-mospi" href="https://www.mospi.gov.in/" target="_blank" rel="noreferrer"><img src="/assets/branding/mospi.png" alt="Ministry of Statistics and Programme Implementation, Government of India"/></a><Link className="brand-paimana" to="/"><img src="/assets/branding/paimana.png" alt="PAIMANA"/></Link><div className="officer-tools"><div className="report-period" title="Current reporting period"><CalendarDays size={20}/><div><span>Reporting Period</span><strong>June 2026</strong></div></div><div className="officer-profile"><span className="avatar">M</span><div><strong>Monitoring Officer</strong><small>Central Monitoring Unit</small></div></div><button className="logout" type="button" onClick={()=>{logout();navigate('/login')}}>Logout</button></div></header>}
