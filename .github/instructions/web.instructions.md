---
applyTo: "web/**/*.ts,web/**/*.tsx,web/**/*.js,web/**/*.jsx"
---

# Web Frontend Rules

Next.js 15 with App Router, deployed to Vercel.

## Conventions

- Functional components only, no class components
- App Router: pages in `web/src/app/`, API routes in `web/src/app/api/`
- Supabase client in `web/src/lib/supabase.ts`
- Auth hook: `useAuth` in `web/src/hooks/`
- Real-time updates via Supabase Realtime (row-level changes on `audits` table)
- Never store secrets client-side — use server-side API routes or environment variables
