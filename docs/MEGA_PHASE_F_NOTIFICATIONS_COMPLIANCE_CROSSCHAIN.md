# Mega Phase F: Notifications + Compliance Scanner + Cross-chain Support

This phase keeps Web3Guard AI by RAADHANEX real-only.

## Notifications

Use `/notifications` to create dry-run/manual preview events. Real delivery requires provider configuration.

Backend env examples:

```env
SMTP_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=security@raadhanex.com

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_DEFAULT_CHAT_ID=...

DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=...
```

WhatsApp requires Twilio/Meta approval and templates, so it is not marked sent by default.

## Compliance Scanner

Use `/compliance` to run readiness checks. Output is not legal advice.

Checks include terms, privacy, refund/scope, GST invoice flow, data deletion, crypto risk disclosure, AML/KYC process, incident response, and safe harbor.

## Cross-chain Scanner

Use `/scanner/cross-chain` for EVM/Solana/Move readiness hints.

EVM checks are source/ABI/notes based. Solana/Move are checklist/static-hint mode only.

No private keys, no wallet connect, no signing, no chain transaction execution.
