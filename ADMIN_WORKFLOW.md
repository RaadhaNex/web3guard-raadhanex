# Phase 4 Admin Workflow

## Admin page
Frontend:
```text
/admin/leads
```

Use backend `.env` value:
```env
ADMIN_TOKEN=your-secret-token
```

## Lead lifecycle
1. New
2. Contacted
3. Payment Pending
4. Paid
5. In Review
6. Delivered
7. Closed
8. Refunded
9. Rejected / Out of Scope

## Payment lifecycle
1. created
2. reference_submitted
3. manual_verification_pending
4. verified
5. failed
6. cancelled

## Safe workflow
- If user submits reference ID, keep payment status as `reference_submitted` or `manual_verification_pending`.
- Check your UPI/bank app manually.
- Only after money is received, set payment status to `verified`.
- Then lead automatically moves to `Paid`.
- Assign reviewer.
- Add internal notes.
- Move to `In Review`.
- Deliver report.
- Move to `Delivered` then `Closed`.

## CSV export
Use CSV export for backup and manual CRM tracking.

## Production future
Replace token admin with real auth and role-based access before scaling.
