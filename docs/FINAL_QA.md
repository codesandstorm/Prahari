# Final QA

## Automated verification

- `npm install`: dependencies present and lockfile respected.
- `npm test -- --run`: 29/29 tests pass.
- `npm run build`: production build passes.
- `npm run preview -- --host 127.0.0.1`: production preview served successfully.
- Route coverage: public, login, all officer portfolio/workflow routes, and all five project routes.
- Interaction coverage: login, project filter/saved view, alert acknowledgement, review note, and deterministic assistant response.

## Viewport inspection

Generated and visually inspected:

- `qa-screenshots/projects-1366x768.png`
- `qa-screenshots/projects-1440x900.png`
- `qa-screenshots/projects-1920x1080.png`

At 1366 and 1440, the main grid remains separate from the 300–320 px rail; wide columns scroll only within the table shell. At 1920, all ten columns, pagination, Saved Views and status legend render simultaneously without overlap. Header, sidebar, launcher, filter wrapping, pills and long project names remain legible.

## Manual flows passed

Landing → Login → Overview → Projects → BHATADI search → dossier → Schedule → Milestones → Ask PRAHARI; Alerts → row selection → detail → acknowledge → review → note/outcome; Saved View → reset → page/rows → secondary project; notifications → mark read; settings → density/reset.

## Accessibility and errors

Protected redirects, labeled inputs, semantic tables, disabled states, visible focus-capable native controls, drawer label/Escape, not-found states, empty states, and readable contrast were checked. No console-breaking production error was observed. The assistant auto-scroll is guarded for environments without `scrollTo`.

## Known non-blockers

- The main JS chunk is about 546 kB minified (about 180 kB gzip); Vite emits a chunk-size advisory.
- Charts remain intentionally lightweight demonstration visuals rather than a full charting package.
- Only Bhatadi has the full five-tab curated dossier; other listed projects show an honest summary rather than fabricated detailed predictions.
- Static hosts require SPA fallback configuration.
