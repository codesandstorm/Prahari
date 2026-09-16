# Final QA

## Automated verification

- `npm install`: dependencies present and lockfile respected.
- `npm test -- --run`: 29/29 tests pass.
- `npm run build`: production build passes.
- `npm run preview -- --host 127.0.0.1`: production preview served successfully.
- Route coverage: public, login, all officer portfolio/workflow routes, and all five project routes.
- Interaction coverage: login, project filter/saved view, alert acknowledgement, review note, and deterministic assistant response.

## Viewport inspection

Generated and visually inspected at 1366×768, 1440×900 and 1920×1080:

- Landing, Overview, Projects, BHATADI overview, Schedule, Execution Health, Analytics, Alerts and Reviews
- Ask PRAHARI open on the BHATADI Schedule page

The resulting 30 captures are in `qa-screenshots/`. The Projects grid remains separate from its rail and wide columns scroll only inside the table. Project pages no longer create document-level horizontal overflow. Cards, charts, legends, map detail, assistant controls, filters and long labels remain legible at all three target sizes.

## Manual flows passed

Landing → Login → Overview → Projects → BHATADI search → dossier → Schedule → Milestones → Ask PRAHARI; Alerts → row selection → detail → acknowledge → review → note/outcome; Saved View → reset → page/rows → secondary project; notifications → mark read; settings → density/reset.

## Accessibility and errors

Protected redirects, labeled inputs, semantic tables, disabled states, visible focus-capable native controls, drawer label/Escape, not-found states, empty states, and readable contrast were checked. The automated browser pass reported zero console errors. The assistant auto-scroll is guarded for environments without `scrollTo`.

## Known non-blockers

- The main JS chunk is about 546 kB minified (about 180 kB gzip); Vite emits a chunk-size advisory.
- Charts are lightweight responsive SVG/CSS visuals; they do not require a charting runtime.
- Only Bhatadi has the full five-tab curated dossier; other listed projects show an honest summary rather than fabricated detailed predictions.
- Static hosts require SPA fallback configuration.
