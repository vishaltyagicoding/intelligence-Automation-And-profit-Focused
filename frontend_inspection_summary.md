# Frontend Dependency Inspection Summary

## Scope
Inspection only. No project source files were modified.

## Files inspected
- `package.json`
- `app/page.tsx`
- `next-env.d.ts`

## Current frontend dependencies
From `package.json`:
- `next`: `15.0.0`
- `react`: `18.3.1`
- `react-dom`: `18.3.1`
- `lightweight-charts`: `4.2.1`

Dev dependencies:
- `@types/react`: `^19.2.14`
- `@types/react-dom`: `^19.2.3`

## Findings
- This repository is set up to be a Next.js TypeScript frontend.
- `app/page.tsx` exists and exports the default page component using the App Router style.
- `next-env.d.ts` exists, confirming Next.js type integration.
- `app/page.tsx` is a client component and uses browser WebSockets for live market and AI signal feeds.
- `app/layout.tsx` could not be read and appears missing from inspection, which is a major issue for a runnable Next App Router app.
- The page imports:
  - `../components/ChartComponent`
  - `../components/Watchlist`
  These could not be verified because directory listing results were inconsistent.

## Standalone runnability
The frontend looks intended to run as a standalone Next app, but it is not confidently runnable as-is based on the inspected files because:
- `package.json` has no visible `scripts` section for `dev`, `build`, or `start`
- `app/layout.tsx` was not found during inspection
- referenced component files were not verifiable

## Docker/runtime considerations
`app/page.tsx` hardcodes the WebSocket base URL to `ws://localhost`:
- market feed: `/ws/market/{asset}/`
- AI signals: `/ws/ai-signals/?token=...`

This is likely to be problematic in Docker because `localhost` inside a frontend container usually points to the frontend container itself, not the backend or reverse proxy.

For Docker, the frontend will likely need one of:
- an environment-driven WebSocket base URL
- same-origin proxying through nginx
- service-name-based internal networking

## Type compatibility concern
There is a version mismatch:
- runtime React: `18.3.1`
- types packages: React 19 major versions

That is not ideal and can cause TypeScript/type-checking issues.

## Keys/endpoints expected by the frontend
Local storage keys used by the page:
- `auth_token`
- `subscription_active`

Backend WebSocket endpoints expected:
- `/ws/market/BTCUSD/`
- `/ws/market/ETHUSD/`
- `/ws/market/XRPUSD/`
- `/ws/market/LTCUSD/`
- `/ws/ai-signals/?token=...`

## Notes
Tooling returned inconsistent filesystem visibility:
- `app/page.tsx` was readable
- `list_files` for `app/` and `components/` returned no files

Because of that, some structure verification was limited.