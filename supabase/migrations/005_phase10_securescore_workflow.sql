-- Phase 10 — SecureScore Pro Dashboard + Finding Workflow
-- Run after previous Phase 7/8/9 migrations if you use Supabase mode.

create table if not exists public.finding_workflow_statuses (
  id text primary key,
  user_id text not null,
  scan_id text not null,
  finding_id text not null,
  workflow_key text not null,
  status text not null default 'open' check (status in ('open','in_progress','fixed','false_positive','accepted_risk','needs_manual_review')),
  notes text,
  assigned_to text,
  source text default 'Phase 10 SecureScore workflow',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  fixed_at timestamptz,
  unique(user_id, workflow_key)
);

alter table public.finding_workflow_statuses enable row level security;

drop policy if exists "Users can read own finding workflows" on public.finding_workflow_statuses;
create policy "Users can read own finding workflows"
  on public.finding_workflow_statuses for select
  using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own finding workflows" on public.finding_workflow_statuses;
create policy "Users can insert own finding workflows"
  on public.finding_workflow_statuses for insert
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can update own finding workflows" on public.finding_workflow_statuses;
create policy "Users can update own finding workflows"
  on public.finding_workflow_statuses for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);

create index if not exists idx_finding_workflow_user_scan on public.finding_workflow_statuses(user_id, scan_id);
create index if not exists idx_finding_workflow_status on public.finding_workflow_statuses(user_id, status);
