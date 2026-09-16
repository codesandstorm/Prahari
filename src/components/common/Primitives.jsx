import React from 'react';
import { AlertTriangle, BarChart3, CheckCircle2, Clock3, Search, ArrowRight } from 'lucide-react';

const icons={alert:AlertTriangle,chart:BarChart3,check:CheckCircle2,clock:Clock3,search:Search};
const tone={red:['#e9334c','#ffe5e9'],amber:['#ef9f00','#fff4d8'],green:['#149e63','#dff7eb'],purple:['#7756c7','#eee8ff'],blue:['#087bd0','#e4f3ff']};

export function StatusPill({children,tone:kind}){const inferred=kind||(/review|high|limited/i.test(children)?'red':/verify|watch|moderate/i.test(children)?'amber':/good|track|complete|resolved/i.test(children)?'green':/monitor|open|stable/i.test(children)?'blue':'purple');return <span className={`pill ${inferred}`}>{children}</span>}
export function KpiCard({item}){const Icon=icons[item.icon]||BarChart3;const [color,soft]=tone[item.tone]||tone.blue;return <article className="kpi-card" style={{'--accent':color,'--accent-soft':soft}}><span className="kpi-icon"><Icon/></span><div><strong>{item.value}</strong><p>{item.label}</p></div></article>}
export function Section({title,action,children,className=''}){return <section className={`surface ${className}`}><header className="section-head"><h2>{title}</h2>{action}</header>{children}</section>}
export function PageHeroHeader({title,subtitle,breadcrumb='Home / Overview',message='Data-driven infrastructure for a stronger India'}){return <header className="page-hero"><div><div className="breadcrumb">{breadcrumb}</div><h1>{title}</h1><p>{subtitle}</p></div><div className="hero-message">“{message}”</div></header>}
export function ActionLink({children,to}){return <a className="text-link" href={to}>{children} <ArrowRight size={14}/></a>}
