-- Phase 9: Professional/Public Report System
-- Run after Phase 7/7.1/7.2/8 migrations when using Supabase/PostgreSQL mode.

create table if not exists public.public_reports (
  id text primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  user_id text,
  project_id text,
  report_id text not null,
  report_hash text not null,
  project_name text,
  visibility text not null default 'private' check (visibility in ('public', 'private')),
  status text not null default 'active' check (status in ('active', 'expired', 'revoked', 'superseded')),
  public_wording text not null default 'Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX',
  manual_review_claim_allowed boolean not null default false,
  report jsonb not null default '{}'::jsonb
);

alter table public.public_reports enable row level security;

create index if not exists public_reports_user_id_idx on public.public_reports(user_id);
create index if not exists public_reports_project_id_idx on public.public_reports(project_id);
create index if not exists public_reports_report_hash_idx on public.public_reports(report_hash);
create index if not exists public_reports_visibility_status_idx on public.public_reports(visibility, status);

-- Public users can read only active public reports.
do $$ begin
  create policy "public_reports_public_read"
  on public.public_reports
  for select
  using (visibility = 'public' and status = 'active');
exception when duplicate_object then null;
end $$;

-- Authenticated users may read/write their own report records when user_id matches auth.uid()::text.
do $$ begin
  create policy "public_reports_owner_read"
  on public.public_reports
  for select
  using (auth.uid()::text = user_id);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "public_reports_owner_insert"
  on public.public_reports
  for insert
  with check (auth.uid()::text = user_id);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "public_reports_owner_update"
  on public.public_reports
  for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);
exception when duplicate_object then null;
end $$;
