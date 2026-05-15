-- Mega Phase G — Security hardening + final QA records
create table if not exists security_audit_log (
  id text primary key,
  created_at timestamptz not null default now(),
  event_type text not null,
  actor text,
  note text
);

create table if not exists final_qa_runs (
  id text primary key,
  created_at timestamptz not null default now(),
  actor text,
  note text,
  readiness text,
  security_score numeric
);

alter table security_audit_log enable row level security;
alter table final_qa_runs enable row level security;

-- Use service-role/admin APIs for writes. Add org-specific policies later if exposing these to tenant admins.
