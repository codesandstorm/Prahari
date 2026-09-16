# Deployment

## Local

```powershell
npm install
npm run dev
npm test
npm run build
npm run preview
```

Production output is `dist/`. The build is a client-side SPA: static hosting must rewrite unknown paths such as `/officer/projects/PRH-400033` to `/index.html`. Assets are rooted under `/assets/`, so deploy at the host root or configure a matching Vite base before a sub-path deployment.

Demo credentials: `sih-demo-officer` / `Prahari@2026`. These are local prototype credentials, not secrets or real authentication. Protected routes depend on a localStorage demo session.

Reset through Settings → Reset demo data. Direct fallback: clear `prahari-v2-demo-state` and `prahari-v2-demo-session` in browser storage, then sign in again.

QA screenshots can be regenerated on Windows while the preview is running with `node scripts/qa-screenshots.mjs`. The script uses installed Edge in headless mode and writes the three required Projects viewport images to `qa-screenshots/`.

No backend URL, API token, government credential, or live prediction endpoint is embedded in this build.
