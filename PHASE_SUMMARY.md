# v3.7 Non-Payment Launch Readiness Patch

## Goal
Keep all payment collection features pending until the final payment phase, while allowing the rest of the product to move toward beta readiness.

## Changed
- Pricing page now shows paid packages as planning/request-only, not checkout-enabled.
- Billing page now clearly states payments are deferred.
- Feature Status page updated with accurate non-payment readiness states.
- Settings dropdown now includes Launch Readiness.
- New Launch Readiness page added.
- Added non-payment launch readiness documentation.

## Real-only rule preserved
- No fake payment success.
- No fake subscription activation.
- No frontend-only paid access.
- UPI/Razorpay remain pending until real verification is implemented.
