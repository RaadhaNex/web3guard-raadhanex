-- Mega Phase D — Phase 25/26/27: Bug bounty readiness, public registry, developer API keys.
-- Run after previous Web3Guard AI by RAADHANEX migrations.
-- These tables are real persistence targets; they do not enable fake escrow, certified audits, or on-chain certificates.

create table if not exists public.bug_bounty_programs (
  id text primary key,
  user_id text,
  organization_id text,
  project_id text,
  project_name text not null,
  website_url text,
  scope_summary text not null,
  in_scope_assets jsonb default '[]'::jsonb,
  out_of_scope_assets jsonb default '[]'::jsonb,
  reward_low_inr integer,
  reward_medium_inr integer,
  reward_high_inr integer,
  reward_critical_inr integer,
  safe_harbor_text text,
  contact_email text,
  contact_handle text,
  status text default 'draft',
  escrow_status text default 'not_enabled_manual_rewards_only',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.bug_bounty_submissions (
  id text primary key,
  program_id text not null references public.bug_bounty_programs(id) on delete cascade,
  researcher_name text,
  researcher_contact text,
  title text not null,
  severity_claimed text default 'medium',
  affected_asset text,
  description text not null,
  reproduction_steps text,
  impact text,
  recommendation text,
  proof_links jsonb default '[]'::jsonb,
  status text default 'submitted',
  triage_notes text,
  final_severity text,
  reward_amount_inr integer,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.public_registry (
  id text primary key,
  user_id text,
  report_id text not null,
  project_name text not null,
  report_hash text not null,
  score integer,
  risk_label text,
  summary text,
  status text default 'active',
  expires_at text,
  public_notes text,
  badge_token text not null,
  public_url text,
  badge_label text default 'Pre-audit readiness reviewed',
  disclaimer text default 'This is a public pre-audit readiness record, not a certified audit or security guarantee.',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.registry_events (
  id text primary key,
  registry_id text not null references public.public_registry(id) on delete cascade,
  event text not null,
  reason text,
  created_at timestamptz default now()
);

create table if not exists public.developer_api_keys (
  id text primary key,
  user_id text,
  organization_id text,
  name text not null,
  key_hash text not null,
  key_prefix text not null,
  permissions jsonb default '[]'::jsonb,
  rate_limit_per_hour integer default 60,
  expires_at text,
  status text default 'active',
  last_used_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.developer_api_events (
  id text primary key,
  api_key_id text references public.developer_api_keys(id) on delete set null,
  permission text,
  created_at timestamptz default now()
);

alter table public.bug_bounty_programs enable row level security;
alter table public.bug_bounty_submissions enable row level security;
alter table public.public_registry enable row level security;
alter table public.registry_events enable row level security;
alter table public.developer_api_keys enable row level security;
alter table public.developer_api_events enable row level security;

-- Service role/backend can manage these tables. Public read policies should be added only after final auth model is selected.
