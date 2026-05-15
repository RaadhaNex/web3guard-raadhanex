-- Web3Guard AI by RAADHANEX — Phase 7 core Supabase schema
-- Purpose: real auth/database/dashboard foundation. No fake audit or fake subscription records.
-- Run inside Supabase SQL editor after creating the project.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  full_name text,
  company_name text,
  preferred_language text not null default 'English',
  plan text not null default 'free',
  role text not null default 'user',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  website_url text,
  chain text,
  contract_address text,
  github_repo_url text,
  project_type text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.scan_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  module text not null,
  project_name text,
  score integer check (score is null or (score >= 0 and score <= 100)),
  risk_label text,
  report_id text,
  input_hash text,
  findings_count integer not null default 0,
  critical_high_count integer not null default 0,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.saved_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  report_id text not null,
  title text not null,
  report_hash text,
  overall_score integer check (overall_score is null or (overall_score >= 0 and overall_score <= 100)),
  available_score integer check (available_score is null or (available_score >= 0 and available_score <= 100)),
  risk_label text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_id text not null default 'free',
  status text not null default 'not_connected_until_phase8_razorpay',
  gateway text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  project_id uuid references public.projects(id) on delete set null,
  package_id text,
  amount_inr integer,
  gateway text not null default 'upi_manual',
  status text not null default 'manual_verification_pending',
  payment_reference text,
  invoice_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.scan_history enable row level security;
alter table public.saved_reports enable row level security;
alter table public.subscriptions enable row level security;
alter table public.payments enable row level security;

-- Profiles: every user can manage only their profile.
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own" on public.profiles for insert with check (auth.uid() = id);
drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

-- Projects.
drop policy if exists "projects_select_own" on public.projects;
create policy "projects_select_own" on public.projects for select using (auth.uid() = user_id);
drop policy if exists "projects_insert_own" on public.projects;
create policy "projects_insert_own" on public.projects for insert with check (auth.uid() = user_id);
drop policy if exists "projects_update_own" on public.projects;
create policy "projects_update_own" on public.projects for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists "projects_delete_own" on public.projects;
create policy "projects_delete_own" on public.projects for delete using (auth.uid() = user_id);

-- Scan history.
drop policy if exists "scan_history_select_own" on public.scan_history;
create policy "scan_history_select_own" on public.scan_history for select using (auth.uid() = user_id);
drop policy if exists "scan_history_insert_own" on public.scan_history;
create policy "scan_history_insert_own" on public.scan_history for insert with check (auth.uid() = user_id);

-- Saved reports.
drop policy if exists "saved_reports_select_own" on public.saved_reports;
create policy "saved_reports_select_own" on public.saved_reports for select using (auth.uid() = user_id);
drop policy if exists "saved_reports_insert_own" on public.saved_reports;
create policy "saved_reports_insert_own" on public.saved_reports for insert with check (auth.uid() = user_id);

-- Payments/subscriptions are readable by owner. Writes are expected from backend service role / Phase 8 Razorpay webhook.
drop policy if exists "subscriptions_select_own" on public.subscriptions;
create policy "subscriptions_select_own" on public.subscriptions for select using (auth.uid() = user_id);
drop policy if exists "payments_select_own" on public.payments;
create policy "payments_select_own" on public.payments for select using (auth.uid() = user_id);

create index if not exists idx_projects_user_created on public.projects(user_id, created_at desc);
create index if not exists idx_scan_history_user_created on public.scan_history(user_id, created_at desc);
create index if not exists idx_saved_reports_user_created on public.saved_reports(user_id, created_at desc);
create index if not exists idx_payments_user_created on public.payments(user_id, created_at desc);

-- Phase 7.1 dashboard/project detail additions. Safe to re-run.
alter table public.projects add column if not exists description text;
alter table public.projects add column if not exists owner_contact text;
alter table public.scan_history add column if not exists status text not null default 'saved';
alter table public.scan_history add column if not exists notes text;
alter table public.saved_reports add column if not exists scan_id uuid references public.scan_history(id) on delete set null;
alter table public.saved_reports add column if not exists visibility text not null default 'private';
alter table public.saved_reports add column if not exists status text not null default 'saved';

drop policy if exists "scan_history_update_own" on public.scan_history;
create policy "scan_history_update_own" on public.scan_history for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "saved_reports_update_own" on public.saved_reports;
create policy "saved_reports_update_own" on public.saved_reports for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

create index if not exists idx_scan_history_project_created on public.scan_history(project_id, created_at desc);
create index if not exists idx_saved_reports_project_created on public.saved_reports(project_id, created_at desc);
