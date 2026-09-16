import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import App from '../app/App';

const renderAt=(path)=>render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>);

describe('PRAHARI Frontend V2 route contracts',()=>{
  it.each([
    ['/', 'Project Monitoring'], ['/login', 'Sign in to PAIMANA'], ['/officer/overview', 'Welcome back, Officer'],
    ['/officer/projects', 'Project list'], ['/officer/attention', 'Attention Queue'], ['/officer/alerts', 'Alert list'],
    ['/officer/alerts/ALRT-2026-0187', 'Alert Lifecycle'], ['/officer/reviews', 'Review Queue'],
    ['/officer/reviews/REV-2026-0143', 'Review Workflow'], ['/officer/monitoring', 'Projects under continued monitoring'],
    ['/officer/analytics', 'Portfolio Progress Trend'], ['/officer/reports', 'Report library'],
    ['/officer/workspace', 'Assigned reviews'], ['/officer/notifications', 'Notification center'], ['/officer/settings', 'Display preferences'],
    ['/officer/projects/PRH-400033', 'Project snapshot'], ['/officer/projects/PRH-400033/schedule', 'Three-month forecast preview'],
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

  it('keeps research preview and evidence boundaries explicit',()=>{
    renderAt('/officer/projects/PRH-400033');
    expect(screen.getAllByText('Research preview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Execution Health').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading',{name:'Milestone Journey'})).toBeInTheDocument();
  });

  it('opens a contextual Ask PRAHARI drawer',()=>{
    renderAt('/officer/projects/PRH-400033/schedule');
    fireEvent.click(screen.getByRole('button',{name:/Ask PRAHARI/}));
    expect(screen.getByLabelText('Ask PRAHARI assistant')).toHaveClass('open');
    expect(screen.getByText('Why is the schedule at risk?')).toBeInTheDocument();
  });
});
