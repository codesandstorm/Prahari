import React, { createContext, useContext, useMemo, useState } from 'react';
import { alerts as alertFixtures } from '../data/mock/alerts';
import { reviews as reviewFixtures } from '../data/mock/reviews';
import { notifications as notificationFixtures } from '../data/mock/supporting';

const STORAGE_KEY='prahari-v2-demo-state';
const SESSION_KEY='prahari-v2-demo-session';
const Context=createContext(null);
const initialNotifications=notificationFixtures.map((n,index)=>({id:`NOT-${index+1}`,type:n[0],text:n[1],date:n[2],read:n[3],route:index===0?'/officer/alerts/ALRT-2026-0187':index===1?'/officer/reviews/REV-2026-0143':index===2?'/officer/projects/PRH-430142':'/officer/monitoring'}));
const defaults={alerts:alertFixtures.map(a=>({...a,history:[['12 Jun 2026, 10:28','System','Alert created']]})),reviews:reviewFixtures.map(r=>({...r,notes:[],completedActions:[0,1],outcome:'Continue monitoring'})),notifications:initialNotifications,settings:{density:'comfortable',landing:'/officer/overview',notifications:true}};
const readState=()=>{try{return {...defaults,...JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}')}}catch{return defaults}};

export function DemoStoreProvider({children}){
 const [state,setState]=useState(readState);const [authenticated,setAuthenticated]=useState(()=>localStorage.getItem(SESSION_KEY)==='true');
 const persist=next=>{setState(next);localStorage.setItem(STORAGE_KEY,JSON.stringify(next))};
 const updateAlert=(id,status,action=status)=>persist({...state,alerts:state.alerts.map(a=>a.id===id?{...a,status,updated:'16 Jun 2026',history:[...a.history,['16 Jun 2026, 14:30','sih-demo-officer',action]]}:a)});
 const startReview=(alert)=>{const existing=state.reviews.find(r=>r.projectId===alert.projectId);if(existing){updateAlert(alert.id,'In review','Review started');return existing.id}const id=`REV-DEMO-${String(state.reviews.length+1).padStart(3,'0')}`;const review={id,project:alert.project,projectId:alert.projectId,type:alert.type,state:'In progress',priority:alert.priority==='High'?'High':'Medium',assigned:'sih-demo-officer',next:'25 Jun 2026',updated:'16 Jun 2026',notes:[],completedActions:[],outcome:'Continue monitoring'};persist({...state,alerts:state.alerts.map(a=>a.id===alert.id?{...a,status:'In review'}:a),reviews:[review,...state.reviews]});return id};
 const addReviewNote=(id,text)=>{if(!text.trim())return;persist({...state,reviews:state.reviews.map(r=>r.id===id?{...r,notes:[...r.notes,{text:text.trim(),date:'16 Jun 2026',author:'sih-demo-officer'}],updated:'16 Jun 2026'}:r)})};
 const updateReview=(id,patch)=>persist({...state,reviews:state.reviews.map(r=>r.id===id?{...r,...patch,updated:'16 Jun 2026'}:r)});
 const toggleReviewAction=(id,index)=>{const r=state.reviews.find(x=>x.id===id);const completed=r.completedActions.includes(index)?r.completedActions.filter(x=>x!==index):[...r.completedActions,index];updateReview(id,{completedActions:completed})};
 const markNotification=(id)=>persist({...state,notifications:state.notifications.map(n=>n.id===id?{...n,read:true}:n)});
 const markAllNotifications=()=>persist({...state,notifications:state.notifications.map(n=>({...n,read:true}))});
 const updateSettings=patch=>persist({...state,settings:{...state.settings,...patch}});
 const resetDemo=()=>{localStorage.removeItem(STORAGE_KEY);setState(defaults)};
 const login=(username,password)=>{if(username==='sih-demo-officer'&&password==='Prahari@2026'){localStorage.setItem(SESSION_KEY,'true');setAuthenticated(true);return true}return false};
 const logout=()=>{localStorage.removeItem(SESSION_KEY);setAuthenticated(false)};
 const value=useMemo(()=>({...state,authenticated,login,logout,updateAlert,startReview,addReviewNote,updateReview,toggleReviewAction,markNotification,markAllNotifications,updateSettings,resetDemo,unreadCount:state.notifications.filter(n=>!n.read).length,activeAlertCount:state.alerts.filter(a=>a.status!=='Resolved').length}),[state,authenticated]);
 return <Context.Provider value={value}>{children}</Context.Provider>
}
export const useDemoStore=()=>useContext(Context);
