# Phase 7.2 — Organization + Team Workspace

## What is live

- Real organization/workspace records
- Owner membership auto-created from a real create action
- Manual member invite records
- Role model: owner, admin, reviewer, member, viewer
- Finding remediation tasks
- Task status workflow
- Workspace comments
- Workspace activity audit trail
- Dashboard pages:
  - `/dashboard/workspace`
  - `/dashboard/workspace/[id]`
- Backend APIs:
  - `GET /workspace/status`
  - `POST /organizations`
  - `GET /organizations`
  - `GET /organizations/{id}`
  - `PATCH /organizations/{id}`
  - `POST /organizations/{id}/members`
  - `GET /organizations/{id}/members`
  - `PATCH /organizations/{id}/members/{member_id}`
  - `POST /workspace/finding-tasks`
  - `GET /workspace/finding-tasks`
  - `PATCH /workspace/finding-tasks/{task_id}`
  - `POST /workspace/comments`
  - `GET /workspace/comments`

## Real-only rule

No fake team data is generated. Member invites are saved as manual invite records only. Phase 7.2 does **not** send email invites, does **not** fake real-time collaboration, and does **not** fake paid seat billing.

## Local mode

By default, workspace data is saved into JSONL files:

- `backend/app/data/db/organizations.jsonl`
- `backend/app/data/db/org_members.jsonl`
- `backend/app/data/db/finding_tasks.jsonl`
- `backend/app/data/db/workspace_comments.jsonl`
- `backend/app/data/db/workspace_activity.jsonl`

## Supabase mode

Run this migration after Phase 7 migration:

```sql
supabase/migrations/002_phase72_workspace_schema.sql
```

Phase 7.2 keeps service-role backend access as the safest MVP path. Direct frontend database access for org membership will be tightened in future production hardening.

## What is still not connected

- Email invitation delivery
- Real-time comments
- Paid team seat billing
- Reviewer marketplace
- External ticket integrations
- Public report registry

These are not shown as live features.
