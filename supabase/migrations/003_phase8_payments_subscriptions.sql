-- Phase 8 — Razorpay + UPI payment/subscription foundation for Web3Guard AI by RAADHANEX.
-- Real-only rule: payment/subscription records should be updated only after Razorpay signature/webhook verification or manual admin approval.

create table if not exists public.payment_intents (
  id text primary key,
  created_at timestamptz not null default now(),
  user_id text,
  organization_id text,
  package_id text not null,
  package_name text not null,
  amount_inr integer not null,
  amount_paise integer not null default 0,
  currency text not null default 'INR',
  billing_cycle text not null default 'one_time',
  customer_name text,
  customer_email text,
  project_name text,
  provider text not null default 'upi_manual',
  provider_preference text not null default 'auto',
  upi_id text,
  upi_name text,
  upi_deep_link text,
  manual_verification_required boolean not null default true,
  razorpay_enabled boolean not null default false,
  razorpay_order_id text,
  razorpay_payment_id text,
  razorpay_receipt text,
  razorpay_order_status text,
  status text not null default 'created',
  verified_at timestamptz,
  webhook_verified_at timestamptz,
  subscription_id text,
  invoice_id text,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists payment_intents_user_idx on public.payment_intents(user_id);
create index if not exists payment_intents_org_idx on public.payment_intents(organization_id);
create index if not exists payment_intents_status_idx on public.payment_intents(status);
create index if not exists payment_intents_razorpay_order_idx on public.payment_intents(razorpay_order_id);

create table if not exists public.subscriptions (
  id text primary key,
  created_at timestamptz not null default now(),
  user_id text,
  organization_id text,
  package_id text not null,
  plan_name text not null,
  billing_cycle text not null,
  amount_inr integer not null,
  currency text not null default 'INR',
  status text not null default 'pending',
  customer_name text,
  customer_email text,
  payment_intent_id text references public.payment_intents(id),
  provider text not null default 'upi_manual',
  current_period_start timestamptz,
  current_period_end timestamptz,
  activated_at timestamptz,
  cancelled_at timestamptz,
  manual_verification_required boolean not null default true,
  notes jsonb not null default '[]'::jsonb
);

create index if not exists subscriptions_user_idx on public.subscriptions(user_id);
create index if not exists subscriptions_org_idx on public.subscriptions(organization_id);
create index if not exists subscriptions_status_idx on public.subscriptions(status);

create table if not exists public.payment_events (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  event_type text not null,
  payment_intent_id text,
  razorpay_order_id text,
  razorpay_payment_id text,
  payload jsonb not null default '{}'::jsonb
);

alter table public.payment_intents enable row level security;
alter table public.subscriptions enable row level security;
alter table public.payment_events enable row level security;

-- MVP note:
-- In production, bind user_id/org_id to auth.uid() or organization membership policies.
-- Keep service role for webhook/admin writes only. Do not expose service role key to frontend.
