# Interaction Matrix

All visible controls were classified as functional, navigational, detail-opening, deliberately disabled, or removed. Cosmetic list/grid controls and unsupported PDF claims were removed.

| Page | Control | Implemented behavior |
|---|---|---|
| Landing | Search | Filters high-value project cards by project, sector, ministry, or location |
| Landing | Officer Login / project card | Opens officer access or a neutral public portfolio section; no workflow language is exposed publicly |
| Landing | Hero arrows, dots | Change slide; carousel auto-rotates and pauses on hover |
| Landing | Ministry/Sector tabs and entities | Switches dataset and updates all summary metrics |
| Landing | India map states | Hover highlights; click pins selection and updates detail panel |
| Landing | Mobile menu | Opens/closes public navigation |
| Login | Show password / submit | Toggles visibility; validates fixed local access credentials |
| Landing | Project carousel | Auto-advances, pauses on hover, supports previous/next and direct dot selection |
| Header | PAIMANA / MoSPI / Logout | Public home / official site / clears session and returns to login |
| Sidebar | All entries | Route navigation with route-derived active state and store-derived badges |
| Overview | View all/details, rows, quick actions | Navigate to the corresponding queue, map, project, review, or reports route |
| Projects | Search / clear | Searches name, code, ministry, agency, sector, state, phase |
| Projects | Six filters | AND-combined controlled filters with reset |
| Projects | Sort | Relevance, name, high concern, or progress ordering |
| Projects | Saved Views | Applies High concern, My review queue, Northern region, or Strategic projects |
| Projects | Pagination | Previous, next, and rows-per-page update the visible records |
| Projects | Open dossier | Opens the selected project; unknown IDs show a safe not-found state |
| Attention | Search, status, assignee, sort | Filters/sorts queue; action opens the selected project |
| Alerts | Search, filters, sort, pagination | Operates on alert store; row selection updates the right rail |
| Alerts | Open alert | Opens the selected alert, never a fixed fallback |
| Alert detail | Back / evidence / linked records | Navigates back, expands evidence, opens project/review |
| Alert detail | Acknowledge, assign review, verify, monitor, resolve, escalate | Updates status, history, and lifecycle in persisted frontend state |
| Reviews | Search, filters, sort, pagination | Operates on shared review store; workload rail derives from that store |
| Review detail | Note | Appends a dated officer note |
| Review detail | Checklist / outcome / next date | Persists action completion, review state/outcome, and next date |
| Monitoring | Search, trend, sort, open | Filters/reorders records and opens project context |
| Reports | Prepare / Export CSV | Downloads deterministic CSV contracts; no false PDF claim |
| Notifications | Notification / Mark all | Marks records read, updates badge, and opens related record |
| Settings | Landing, density, notifications | Persists settings locally; compact density visibly changes tables |
| Settings | Reset Experience | Two-step confirmation restores workflows, notifications, preferences and assistant history |
| Project dossier | Tabs / evidence links / workflow actions | SPA navigation to evidence routes and linked review/attention flow |
| Milestone Journey | Milestone node | Selects stage and shows date, state, variance, and evidence |
| Analytics | Analysis window | Controlled selector updates the trend context |
| Analytics | India map | Hover previews and click pins a state; project, attention, progress and revision details update |
| Analytics | Chart marks | Native SVG/segment tooltips expose series labels, counts and units |
| Execution Health | Signal card | Selects a signal family and updates the evidence detail panel |
| Ask PRAHARI | Launcher, minimize, close, clear, prompts, input/send, Escape | Contextual conversation through `AssistantService`, persisted history, typing state and safe fallback |

Status pills, metric tiles, reporting period text, and chart legends are intentionally informational and do not imply click behavior.
