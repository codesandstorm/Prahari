# PRAHARI Frontend V2

Clean-slate, frontend-only PAIMANA/PRAHARI officer experience. It is intentionally isolated from the legacy `Frontend` folder and currently uses governed mock data only.

## Run locally

```powershell
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The officer login is a prototype transition; the prefilled credentials are not connected to government SSO.

## Verify

```powershell
npm test
npm run build
```

## Product boundaries

- Public experience remains PAIMANA-first and identifies MoSPI correctly.
- Schedule and cost values are clearly marked as research previews, not released predictions.
- Final-cost/EAC truth is shown as unavailable where it is not verified.
- Execution Health exposes observable signals without asserting unverified causes.
- Synthetic, historical, and research concepts are never silently blended.
- Alerts and reviews are mock workflow demonstrations and do not mutate a backend.

See the `docs` directory for routes, components, mock contracts, assets, and backend handoff notes.
