import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import App from '../app/App';
import { DemoStoreProvider } from '../state/DemoStore';

const renderAt=(path)=>{if(path.startsWith('/officer'))localStorage.setItem('prahari-v2-demo-session','true');return render(<MemoryRouter initialEntries={[path]}><DemoStoreProvider><App/></DemoStoreProvider></MemoryRouter>)};

describe('PRAHARI Frontend V2 route contracts',()=>{
  beforeEach(()=>localStorage.clear());
  it.each([
    ['/', 'Project Monitoring'], ['/login', 'Sign in to PAIMANA'], ['/officer/overview', 'Welcome back, Officer'],
    ['/officer/projects', 'Project list'], ['/officer/attention', 'Attention Queue'], ['/officer/alerts', 'Alert list'],
    ['/officer/alerts/ALRT-2026-0187', 'Alert Lifecycle'], ['/officer/reviews', 'Review Queue'],
    ['/officer/reviews/REV-2026-0143', 'Review Workflow'], ['/officer/monitoring', 'Projects under continued monitoring'],
    ['/officer/analytics', 'Portfolio Progress Trend'], ['/officer/reports', 'Report library'],
    ['/officer/workspace', 'Assigned reviews'], ['/officer/notifications', 'Notification center'], ['/officer/settings', 'Display preferences'],
    ['/officer/projects/PRH-400033', 'Project snapshot'], ['/officer/projects/PRH-400033/schedule', 'Three-month forecast'],
    ['/officer/projects/PRH-400033/cost', 'Cost-risk contributors'], ['/officer/projects/PRH-400033/execution-health', 'Execution Health signals'],
    ['/officer/projects/PRH-400033/milestones', 'Milestone register'],
  ])('renders %s',(route,expected)=>{
    renderAt(route);
    expect(document.body).toHaveTextContent(expected);
  });

  it('renders the public PAIMANA-first portal',()=>{
    renderAt('/');
    expect(screen.getByRole('heading',{name:'Project Monitoring'})).toBeInTheDocument();
    expect(screen.getByRole('link',{name:'Officer Login'})).toHaveAttribute('href','/login');
    expect(screen.getByText('State-wise Projects')).toBeInTheDocument();
  });

  it('enters the officer workspace through prototype login',()=>{
    renderAt('/login');
    fireEvent.submit(screen.getByRole('button',{name:'Login to Officer Workspace'}).closest('form'));
    expect(screen.getByRole('heading',{name:/Welcome back/})).toBeInTheDocument();
  });

  it('renders portfolio workflow pages without changing the common shell',()=>{
    renderAt('/officer/alerts');
    expect(screen.getByRole('heading',{name:'Alerts'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:/Ask PRAHARI/})).toBeInTheDocument();
    expect(screen.getByRole('link',{name:'Projects'})).toBeInTheDocument();
  });

  it('keeps decision support and evidence boundaries explicit',()=>{
    renderAt('/officer/projects/PRH-400033');
    expect(screen.getAllByText(/Forecast/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Execution Health').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading',{name:'Milestone Journey'})).toBeInTheDocument();
  });

  it('opens a contextual Ask PRAHARI drawer',()=>{
    renderAt('/officer/projects/PRH-400033/schedule');
    fireEvent.click(screen.getByRole('button',{name:/Ask PRAHARI/}));
    expect(screen.getByLabelText('Ask PRAHARI assistant')).toHaveClass('open');
    expect(screen.getByText('Why is the schedule at risk?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Minimize Ask PRAHARI'}));
    expect(screen.getByLabelText('Ask PRAHARI assistant')).toHaveClass('minimized');
  });

  it('filters projects and activates a saved view',()=>{
    renderAt('/officer/projects');
    fireEvent.change(screen.getByLabelText('Search'),{target:{value:'Bhatadi'}});
    expect(screen.getByText(/BHATADI EXPANSION OC/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:/High concern/}));
    expect(screen.getByRole('button',{name:/High concern/})).toHaveClass('active');
  });

  it('persists an alert acknowledgement in the workflow state',()=>{
    renderAt('/officer/alerts/ALRT-2026-0187');
    fireEvent.click(screen.getByRole('button',{name:'Acknowledge'}));
    expect(screen.getAllByText('Acknowledged').length).toBeGreaterThan(0);
    expect(screen.getByText('Alert acknowledged')).toBeInTheDocument();
  });

  it('adds an officer review note',()=>{
    renderAt('/officer/reviews/REV-2026-0143');
    fireEvent.change(screen.getByPlaceholderText('Add an evidence-backed review note'),{target:{value:'Source checked for demo.'}});
    fireEvent.click(screen.getByRole('button',{name:'Add note'}));
    expect(screen.getByText('Source checked for demo.')).toBeInTheDocument();
  });

  it('answers a curated Ask PRAHARI question deterministically',async()=>{
    renderAt('/officer/projects/PRH-400033/schedule');
    fireEvent.click(screen.getByRole('button',{name:/Ask PRAHARI/}));
    fireEvent.click(screen.getByRole('button',{name:/Why is the schedule at risk/}));
    await waitFor(()=>expect(screen.getByText(/physical progress remains behind/i)).toBeInTheDocument(),{timeout:1800});
  });
});
