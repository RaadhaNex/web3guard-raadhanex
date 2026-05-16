-- Phase 4 — Admin payment audit trail foundation.
-- Safe to run multiple times. Keeps a DB-side audit destination for manual UPI verification,
-- Razorpay webhook verification, subscription activation, and admin payment decisions.

create table if not exists public.admin_payment_actions (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  actor_user_id uuid references auth.users(id) on delete set null,
  actor_label text,
  payment_intent_id text,
  subscription_id text,
  action_type text not null,
  old_status text,
  new_status text,
  payment_reference text,
  note text,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists admin_payment_actions_payment_idx on public.admin_payment_actions(payment_intent_id);
create index if not exists admin_payment_actions_subscription_idx on public.admin_payment_actions(subscription_id);
create index if not exists admin_payment_actions_created_idx on public.admin_payment_actions(created_at desc);

alter table public.admin_payment_actions enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'admin_payment_actions'
      and policyname = 'admin payment actions service role only'
  ) then
    create policy "admin payment actions service role only"
    on public.admin_payment_actions
    for all
    using (false)
    with check (false);
  end if;
end $$;

comment on table public.admin_payment_actions is 'Audit trail for manual UPI verification, Razorpay webhook verification, and subscription/payment admin actions. Writes should be done server-side with service role only.';
