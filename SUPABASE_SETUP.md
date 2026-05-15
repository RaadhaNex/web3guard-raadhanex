# Supabase Setup Guide — Web3Guard AI by RAADHANEX

1. Create a Supabase project.
2. Open SQL Editor.
3. Paste and run `supabase/migrations/001_phase7_core_schema.sql`.
4. Copy project URL and anon key into `frontend/.env.local`.
5. Copy project URL, anon key, and service role key into `backend/.env`.
6. Keep `SUPABASE_SERVICE_ROLE_KEY` private and backend-only.
7. Restart backend and frontend.
8. Open `/auth/signup` and create a real account.
9. Open `/dashboard`.
10. Check backend `/db/status`.

## Recommended Supabase Auth settings

For MVP testing:

- Email/password signups enabled.
- Email confirmation can be ON or OFF depending on your testing flow.
- Site URL: `http://localhost:3000` locally.
- Redirect URLs:
  - `http://localhost:3000/auth/login`
  - `http://localhost:3000/dashboard`

## Production checklist

Before launch:

- Set production Site URL.
- Set production redirect URLs.
- Keep RLS enabled.
- Never expose service role key.
- Set strong backend admin token.
- Set `SUPABASE_JWT_VERIFY_ENABLED=true`.
- Set `APP_ENV=production`.
