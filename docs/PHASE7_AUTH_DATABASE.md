# Phase 7 — Supabase Auth + Database + User Dashboard Foundation

## What is live in this phase

Phase 7 adds a real auth/database foundation without faking SaaS data:

- Supabase Auth client in the frontend.
- `/auth/signup` and `/auth/login` pages.
- `/dashboard` page.
- Local JSONL persistence by default so the project runs without cloud setup.
- Supabase-ready backend storage adapter.
- Supabase SQL migration with RLS policies.
- Backend database APIs:
  - `GET /db/status`
  - `POST /profile`
  - `GET /dashboard/overview`
  - `POST /projects`
  - `GET /projects`
  - `POST /scan-history`
  - `GET /scan-history`
  - `POST /saved-reports`
  - `GET /saved-reports`

## Real-only rule

The dashboard does not generate fake projects, fake scans, fake reports, fake subscriptions, or fake audit status.

If you click the dashboard test buttons, the records are saved as real local/Supabase persistence test records and explicitly labelled as test records, not certified audit results.

## Local mode

Default `.env` values use:

```env
STORAGE_MODE=local
LOCAL_DEMO_USER_ID=local-demo-user
```

This writes records to:

```text
backend/app/data/db/profiles.jsonl
backend/app/data/db/projects.jsonl
backend/app/data/db/scan_history.jsonl
backend/app/data/db/saved_reports.jsonl
```

## Supabase mode

Set these in `backend/.env`:

```env
STORAGE_MODE=supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_VERIFY_ENABLED=true
```

Set these in `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Then run the migration:

```text
supabase/migrations/001_phase7_core_schema.sql
```

## Important security note

`SUPABASE_SERVICE_ROLE_KEY` must stay backend-only. Never put it in frontend `.env.local`.

## What is still not live

- Razorpay verified subscriptions are not live until Phase 8.
- The dashboard does not claim a paid plan is active.
- Backend JWT verification is env-gated. In local mode, `user_id` is accepted for development testing.
- Real scanner auto-save from every scanner UI is prepared but not forced yet; the persistence APIs are live for integration.
