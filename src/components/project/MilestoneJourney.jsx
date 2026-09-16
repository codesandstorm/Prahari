import React from 'react';
import { Check, CircleAlert, Clock3 } from 'lucide-react';
import { milestones } from '../../data/mock/projectDetail';
const Icon=({state})=>state==='completed'?<Check/>:state==='delayed'||state==='risk'?<CircleAlert/>:<Clock3/>;
export default function MilestoneJourney({items=milestones}){return <div className="milestone-journey">{items.map((m,i)=><div className={`milestone ${m.state}`} key={m.name}><div className="milestone-line"/><span className="milestone-dot"><Icon state={m.state}/></span><strong>{m.name}</strong><small>{m.date}</small><em>{m.state==='risk'?'At risk':m.state}</em></div>)}</div>}
