# PAIMANA / PRAHARI Frontend

A modular React + Vite application that keeps the existing PAIMANA portal styling and provides PRAHARI Intelligence routes.

## Structure

- `src/components/layout` — PAIMANA portal shell
- `src/components/common` — shared PRAHARI primitives
- `src/components/charts` — portfolio and analytics visualizations
- `src/components/tables` — review queue table
- `src/pages/paimana` — PAIMANA landing page
- `src/pages/prahari` — PRAHARI routes
- `src/data` — current demo data
- `src/services` — future backend integration boundary
- `src/hooks` — reusable data hooks
- `src/styles` — global application styles

## Scripts

```bash
npm run dev
npm run build
npm run preview
```

PRAHARI routes are served through the hash router, for example `#/prahari` and `#/prahari/analytics`.
