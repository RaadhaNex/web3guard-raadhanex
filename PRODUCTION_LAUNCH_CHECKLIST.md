# Production Launch Checklist

## Must pass before public launch
- [ ] Backend `/health` and `/health/readiness` pass.
- [ ] Frontend `npm run build` passes locally.
- [ ] `/security-hardening` has no critical blockers.
- [ ] `/production-qa` reviewed.
- [ ] Admin token changed.
- [ ] Production CORS set to exact domain.
- [ ] Supabase migrations applied.
- [ ] RLS reviewed.
- [ ] Razorpay test mode verified.
- [ ] Razorpay webhook signature verified.
- [ ] UPI fallback verified manually.
- [ ] Privacy/Terms/Refund/Responsible Use lawyer/CA reviewed.
- [ ] No fake counters/testimonials/certified-audit wording.
- [ ] Scanner disclaimers visible.
- [ ] Private/internal URL blocking tested.
- [ ] Public registry badge says “pre-audit readiness reviewed.”
- [ ] Data deletion/contact process documented.
- [ ] Monitoring and notification providers disabled unless configured.
- [ ] Static/deep analysis tools isolated before public untrusted scans.

## Good beta launch scope
Launch as: **Pre-audit readiness MVP beta**.

Do not launch as: certified audit, insurance, formal verification, full penetration testing, or guaranteed protection.
