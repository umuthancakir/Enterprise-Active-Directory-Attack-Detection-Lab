# platform/frontend

Next.js (App Router) + TypeScript + Tailwind dashboard: run a scenario,
view run history and per-run findings, and an ATT&CK coverage heatmap.

## Pages

| Route | Purpose |
|---|---|
| `/` | Dashboard — pick a scenario, trigger a dry-run, view run history |
| `/runs/[id]` | Findings for one run |
| `/coverage` | ATT&CK coverage heatmap from `GET /coverage` |
| `/login` | Sign in (stores the JWT in `localStorage`) |

## Running locally

```bash
cd platform/frontend
npm install
npm run dev
# http://localhost:3000 — set NEXT_PUBLIC_API_BASE_URL in .env first
```

## Status — the least-validated part of this project

**Written, not run.** This machine has no Node.js/npm install (same
Homebrew-blocked story as Packer/QEMU — see `ROADMAP.md` "Known
blockers"), so unlike `platform/backend/` (19 passing tests) or
`attack/`/`detections/` (real pytest coverage), nothing here has been:

- `npm install`-ed (dependency versions in `package.json` are
  best-effort-current, not lockfile-pinned — no `package-lock.json` exists
  yet),
- type-checked (`tsc --noEmit`),
- linted (`eslint`),
- or rendered in a browser.

Treat every `.tsx`/`.ts` file here as a careful first draft. The types in
`src/lib/types.ts` are hand-kept in sync with
`platform/backend/app/schemas.py` — no generated client, so a backend
schema change won't automatically surface here as a type error until
someone actually runs `tsc`.

CI's `frontend` job (`.github/workflows/ci.yml`) will be the first real
validation, whenever this branch is pushed — that job runs `npm install`
(not `npm ci`, since there's no lockfile), `eslint`, `tsc --noEmit`, and
`npm test` (currently a no-op placeholder — see `package.json`).
