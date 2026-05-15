-- Mega Phase E — Phase 28/29/30
-- CI/CD templates, Learning Center progress, Admin Super Panel v2 metadata.
-- Real-only note: these tables store real user/admin records only. They do not fake CI runs, certificates, or system metrics.

create table if not exists public.learning_progress (
  id text primary key,
  user_id text not null,
  lesson_id text not null,
  status text not null check (status in ('started', 'completed', 'bookmarked')),
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.admin_feature_flags (
  id text primary key,
  key text not null unique,
  enabled boolean not null default false,
  note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz,
  updated_by text
);

create table if not exists public.admin_audit_log (
  id text primary key,
  action text not null,
  summary text not null,
  actor text,
  target_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.learning_progress enable row level security;
alter table public.admin_feature_flags enable row level security;
alter table public.admin_audit_log enable row level security;

-- Policies should be tightened with real auth roles before production.
-- Local MVP backend can also use service-role operations behind ADMIN_TOKEN.
