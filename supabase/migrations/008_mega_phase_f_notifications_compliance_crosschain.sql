-- Mega Phase F: Phase 31 Notifications, Phase 32 Compliance Scanner, Phase 33 Cross-chain Support
-- Real-only persistence tables. No fake sends/legal opinions/chain audit certifications are recorded.

create table if not exists public.notification_preferences (
  id text primary key,
  user_id uuid references auth.users(id) on delete set null,
  organization_id text,
  channels jsonb not null default '[]'::jsonb,
  event_types jsonb not null default '[]'::jsonb,
  email text,
  telegram_chat_id text,
  discord_webhook_url text,
  whatsapp_number text,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.notification_events (
  id text primary key,
  user_id uuid references auth.users(id) on delete set null,
  event_type text not null,
  channels jsonb not null default '[]'::jsonb,
  title text not null,
  message text not null,
  severity text not null default 'info',
  dry_run boolean not null default true,
  payload_hash text,
  delivery_results jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.compliance_scans (
  id text primary key,
  user_id uuid references auth.users(id) on delete set null,
  project_name text not null,
  project_type text,
  jurisdictions jsonb not null default '[]'::jsonb,
  score integer,
  readiness_label text,
  findings jsonb not null default '[]'::jsonb,
  manual_review_required boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.cross_chain_scans (
  id text primary key,
  user_id uuid references auth.users(id) on delete set null,
  project_name text,
  chain_family text not null,
  chains jsonb not null default '[]'::jsonb,
  score integer,
  findings jsonb not null default '[]'::jsonb,
  manual_review_required boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.notification_preferences enable row level security;
alter table public.notification_events enable row level security;
alter table public.compliance_scans enable row level security;
alter table public.cross_chain_scans enable row level security;

create policy if not exists "notification preferences owner read" on public.notification_preferences for select using (auth.uid() = user_id);
create policy if not exists "notification preferences owner insert" on public.notification_preferences for insert with check (auth.uid() = user_id);
create policy if not exists "notification events owner read" on public.notification_events for select using (auth.uid() = user_id);
create policy if not exists "notification events owner insert" on public.notification_events for insert with check (auth.uid() = user_id);
create policy if not exists "compliance scans owner read" on public.compliance_scans for select using (auth.uid() = user_id);
create policy if not exists "compliance scans owner insert" on public.compliance_scans for insert with check (auth.uid() = user_id);
create policy if not exists "cross chain scans owner read" on public.cross_chain_scans for select using (auth.uid() = user_id);
create policy if not exists "cross chain scans owner insert" on public.cross_chain_scans for insert with check (auth.uid() = user_id);
