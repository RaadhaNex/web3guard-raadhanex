-- Phase 7.2 — Organization + Team Workspace foundation
-- Run after 001_phase7_core_schema.sql.
-- These tables are real workspace persistence tables. Email invite delivery and paid seat billing are not enabled in Phase 7.2.

create table if not exists public.organizations (
  id text primary key,
  owner_user_id text not null,
  name text not null,
  website_url text,
  billing_email text,
  gst_number text,
  notes text,
  plan text not null default 'free',
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.organization_members (
  id text primary key,
  organization_id text not null references public.organizations(id) on delete cascade,
  user_id text,
  email text,
  full_name text,
  role text not null check (role in ('owner','admin','reviewer','member','viewer')),
  status text not null default 'invited' check (status in ('active','invited','removed')),
  invited_by_user_id text,
  note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.finding_tasks (
  id text primary key,
  organization_id text not null references public.organizations(id) on delete cascade,
  project_id text,
  scan_id text,
  report_id text,
  finding_id text,
  title text not null,
  module text not null default 'general',
  severity text not null default 'medium' check (severity in ('critical','high','medium','low','info')),
  status text not null default 'open' check (status in ('open','in_progress','fixed','false_positive','accepted_risk','needs_manual_review')),
  assigned_to_member_id text,
  assigned_to_user_id text,
  due_date text,
  recommendation text,
  evidence jsonb not null default '{}'::jsonb,
  created_by_user_id text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.workspace_comments (
  id text primary key,
  organization_id text not null references public.organizations(id) on delete cascade,
  project_id text,
  scan_id text,
  report_id text,
  finding_task_id text,
  body text not null,
  created_by_user_id text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.workspace_activity (
  id text primary key,
  organization_id text not null references public.organizations(id) on delete cascade,
  type text not null check (type in ('organization','member','project','scan','report','task','comment')),
  title text not null,
  subtitle text,
  created_by_user_id text,
  target_id text,
  created_at timestamptz not null default now()
);

alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.finding_tasks enable row level security;
alter table public.workspace_comments enable row level security;
alter table public.workspace_activity enable row level security;

-- Service-role backend access should be used for Phase 7.2 APIs.
-- Direct browser Supabase queries are intentionally not required yet.
-- Future phases can replace these broad service-role policies with auth.uid()-based org membership policies.

drop policy if exists "service role can manage organizations" on public.organizations;
create policy "service role can manage organizations" on public.organizations
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

drop policy if exists "service role can manage organization members" on public.organization_members;
create policy "service role can manage organization members" on public.organization_members
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

drop policy if exists "service role can manage finding tasks" on public.finding_tasks;
create policy "service role can manage finding tasks" on public.finding_tasks
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

drop policy if exists "service role can manage workspace comments" on public.workspace_comments;
create policy "service role can manage workspace comments" on public.workspace_comments
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

drop policy if exists "service role can manage workspace activity" on public.workspace_activity;
create policy "service role can manage workspace activity" on public.workspace_activity
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
