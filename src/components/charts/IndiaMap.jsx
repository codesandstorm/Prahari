import React, { useState } from 'react';
import India from '@svg-maps/india';

const values={'Maharashtra':168,'Madhya Pradesh':124,'Uttar Pradesh':152,'Rajasthan':104,'Gujarat':112,'Karnataka':88,'Tamil Nadu':96,'Odisha':74,'West Bengal':82,'Assam':46};
const normalize=name=>name==='Orissa'?'Odisha':name;
const color=n=>!n?'#d8eaf6':n>140?'#075392':n>100?'#1681bd':n>70?'#4aa6d6':'#98ccec';
export default function IndiaMap({compact=false}){const [hover,setHover]=useState(null);const [selected,setSelected]=useState('Maharashtra');const active=hover||selected;return <div className={`india-map ${compact?'compact':''}`}><svg viewBox={India.viewBox} role="img" aria-label="State-wise project overview">{India.locations.map(loc=>{const name=normalize(loc.name);return <path key={loc.id} d={loc.path} fill={color(values[name])} className={active===name?'active':''} tabIndex="0" role="button" aria-label={`${name}: ${values[name]??'summary unavailable'}`} onMouseEnter={()=>setHover(name)} onMouseLeave={()=>setHover(null)} onFocus={()=>setHover(name)} onBlur={()=>setHover(null)} onClick={()=>setSelected(name)}/>})}</svg><div className="map-caption"><strong>{active}</strong><span>{values[active]??'No verified summary'} {values[active]?'projects':''}</span></div><div className="map-scale"><i/><i/><i/><i/></div></div>}
