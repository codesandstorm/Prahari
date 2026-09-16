import React from 'react';
import { Grid2X2, List, RotateCcw, Search } from 'lucide-react';
import { KpiCard, PageHeroHeader, Section, StatusPill } from './Primitives';

export function KpiStrip({items}){return <div className="kpi-grid">{items.map(i=><KpiCard key={i.label} item={i}/>)}</div>}
export function FilterBar({labels=['Ministry','Sector','State','Data Quality']}){return <div className="filter-bar"><label className="search-input"><Search size={18}/><input placeholder="Search by project, code, ministry or keyword"/></label><div className="filter-row">{labels.map(label=><label key={label}><span>{label}</span><select aria-label={label}><option>All</option><option>Needs attention</option><option>Monitor</option><option>Good</option></select></label>)}<button className="reset-filter" type="button"><RotateCcw size={16}/>Reset</button><div className="view-toggle" aria-label="View style"><button className="active" aria-label="List view"><List size={17}/></button><button aria-label="Grid view"><Grid2X2 size={17}/></button></div></div></div>}
export function StandardTable({columns,rows,renderCell}){return <div className="table-scroll"><table className="data-table"><thead><tr>{columns.map(c=><th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={row.id||index}>{columns.map(c=><td key={c.key}>{renderCell?renderCell(row,c.key):String(row[c.key]??'—')}</td>)}</tr>)}</tbody></table></div>}
export function MetricPage({title,subtitle,kpis,filters,children,rail}){return <div className="page"><PageHeroHeader title={title} subtitle={subtitle}/>{kpis&&<KpiStrip items={kpis}/>} {filters&&<FilterBar labels={filters}/>}<div className={rail?'content-grid':''}>{children}{rail}</div></div>}
export function ToneValue({children}){return <StatusPill>{children}</StatusPill>}
export {Section,StatusPill,PageHeroHeader};
