# SureFlow AI — Frontend

The Next.js 16 web application for [SureFlow AI](../README.md). Runs on the host (it is deliberately
not part of `docker-compose.yml`) and talks to the FastAPI backend on port 8000.

---

## Running it

The backend must be up first — see the [root README](../README.md#-quick-start).

```bash
npm install
npm run dev          # → http://localhost:3000
```

| Script | Does |
|---|---|
| `npm run dev` | Dev server with hot reload (Turbopack) |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint |
| `npx tsc --noEmit` | Typecheck |

## Configuration

No `.env` is required. `src/lib/api.ts` defaults to `http://localhost:8000/api/v1`, which matches the
backend's default port. To point somewhere else, create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Structure

```
src/
├── app/
│   ├── page.tsx           # public landing page
│   ├── login/             # authentication
│   └── industrial/        # the application — overview, equipment, copilot,
│                          # maintenance, compliance, lessons, alerts,
│                          # work orders, trends, search, HQ
├── components/
│   ├── landing/           # marketing page sections
│   ├── industrial/        # dashboard widgets
│   └── layout/            # Sidebar, shell
├── lib/
│   ├── api.ts             # Axios client, SSE streaming, auth interceptor
│   ├── AuthContext.tsx    # session state + route guards
│   └── store.ts           # Zustand store
└── types/
```

## Notes

**Auth.** `AuthContext` holds the session in `localStorage` under `sureflow_token` and
`sureflow_user`. Both must be present for a session to count as valid — a half-written session is
cleared automatically, which is what prevents a redirect loop between `/login` and `/industrial`.
A `401` from the API clears the whole session and returns you to login.

**Streaming.** Copilot responses and document-upload progress arrive over SSE via raw `fetch`, not
Axios — so the Axios interceptors don't apply and those calls attach their bearer token explicitly.

**Next.js version.** This is Next 16 with the App Router; APIs and conventions differ from older
versions. Consult the bundled docs in `node_modules/next/dist/docs/` rather than assuming.
