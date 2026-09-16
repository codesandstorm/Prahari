import React from 'react';
import { NavLink } from 'react-router-dom';
import { projectDetail as p } from '../../data/mock/projectDetail';
const tabs=[['Overview',''],['Schedule','/schedule'],['Cost','/cost'],['Execution Health','/execution-health'],['Milestones','/milestones']];
export default function ProjectHeader(){const base=`/officer/projects/${p.id}`;return <><header className="project-hero"><div className="breadcrumb">Home / Projects / {p.name}</div><span className="category-chip">{p.category}</span><h1>{p.name}</h1><strong>Project Code: {p.id}</strong><p>{p.ministry}<i/>Sector: {p.sector}<i/>Implementing Agency: {p.agency}</p><span className="last-updated">Last updated · {p.updated}</span></header><nav className="project-tabs" aria-label="Project intelligence"><>{tabs.map(([label,path])=><NavLink end={!path} key={label} to={`${base}${path}`}>{label}</NavLink>)}</></nav></>}
