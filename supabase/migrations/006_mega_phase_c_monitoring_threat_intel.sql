-- Mega Phase C — Phase 23 Monitoring Lite + Phase 24 Threat Intelligence Feed
-- Real-only MVP tables. These do not imply certified audits, guaranteed monitoring, or live threat feeds.

create table if not exists public.monitoring_configs (
  id text primary key,
  user_id text,
  organization_id text,
  project_name text not null,
  contract_address text not null,
  chain text not null default 'ethereum',
  watch_types jsonb not null default '[]'::jsonb,
  alert_channels jsonb not null default '["dashboard"]'::jsonb,
  notification_target text,
  ownership_verified boolean not null default false,
  status text not null default 'active_manual_ready',
  rpc_configured boolean not null default false,
  notes text,
  real_only_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.monitoring_alerts (
  id text primary key,
  config_id text references public.monitoring_configs(id) on delete cascade,
  project_name text,
  contract_address text,
  chain text,
  event_type text not null,
  severity text not null default 'medium',
  description text not null,
  tx_hash text,
  source text not null default 'manual_admin',
  evidence jsonb not null default '{}'::jsonb,
  notification_status text not null default 'dashboard_recorded_only',
  real_only_note text,
  created_at timestamptz not null default now()
);

create table if not exists public.monitoring_events (
  id text primary key,
  config_id text references public.monitoring_configs(id) on delete cascade,
  chain text,
  from_block bigint,
  to_block bigint,
  logs_detected integer not null default 0,
  alerts_stored integer not null default 0,
  source text not null default 'rpc_check',
  created_at timestamptz not null default now()
);

create table if not exists public.threat_intel_entries (
  id text primary key,
  title text not null,
  protocol_name text,
  chain text,
  category text not null default 'other',
  severity text not null default 'medium',
  summary text not null,
  technical_notes text,
  affected_project_types jsonb not null default '[]'::jsonb,
  relevance_tags jsonb not null default '[]'::jsonb,
  source_url text,
  source_label text,
  amount_lost_usd bigint,
  incident_date text,
  curated_by text,
  status text not null default 'manual_curated',
  live_verified boolean not null default false,
  real_only_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.monitoring_configs enable row level security;
alter table public.monitoring_alerts enable row level security;
alter table public.monitoring_events enable row level security;
alter table public.threat_intel_entries enable row level security;

-- Service-role backend should be used for production writes until app-level auth/roles are finalized.
-- Add user/org policies during production hardening once JWT/user mapping is fully active.
