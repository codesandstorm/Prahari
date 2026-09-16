import React from 'react';
import { Check, CircleAlert, Clock3 } from 'lucide-react';
import { milestones } from '../../data/mock/projectDetail';
const Icon=({state})=>state==='completed'?<Check/>:state==='delayed'||state==='risk'?<CircleAlert/>:<Clock3/>;
export default function MilestoneJourney({items=milestones,onSelect,selected}){return <div className="milestone-journey">{items.map(m=><button type="button" onClick={()=>onSelect?.(m)} className={`milestone ${m.state} ${selected===m.name?'selected':''}`} key={m.name}><span className="milestone-line"/><span className="milestone-dot"><Icon state={m.state}/></span><strong>{m.name}</strong><small>{m.date}</small><em>{m.state==='risk'?'At risk':m.state}</em></button>)}</div>}
