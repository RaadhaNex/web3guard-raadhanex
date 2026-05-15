# Mega Phase F — Phase 31 + 32 + 33

## Included

### Phase 31 — Notifications
- Notification preference records
- Notification event records
- Dry-run/manual preview mode
- Optional SMTP email provider
- Optional Telegram Bot provider
- Optional Discord webhook provider
- WhatsApp provider placeholder with explicit manual-required state until Twilio/Meta templates are configured
- No fake sent status

### Phase 32 — Compliance Scanner
- India VDA, GDPR, MiCA/FATF-style, and general Web3 readiness checks
- Terms/privacy/refund/GST/data deletion/risk disclosure/incident response/safe harbor checks
- Compliance score and findings
- Clear disclaimer: not legal advice

### Phase 33 — Cross-chain Support
- EVM multi-chain metadata and static hints
- Solana Anchor checklist/static hints
- Move/Sui/Aptos checklist/static hints
- Replay/domain separator, cross-chain message validation, oracle freshness, delegatecall, signer/account/object ownership hints
- No wallet connect, no signing, no fake complete chain audit

## Manual accounts/config needed

- SMTP provider or Resend/SendGrid equivalent for real email delivery
- Telegram BotFather bot token + chat ID for Telegram alerts
- Discord webhook URL for Discord alerts
- Twilio/Meta WhatsApp Business account + approved templates for WhatsApp alerts
- Legal/CA review for compliance pages before public commercial launch

## Real-only status

If providers are not configured, notification events are saved as `dry_run_preview` or `manual_required`. The app does not pretend messages were delivered.
