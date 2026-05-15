# Final Implementation Handoff — Web3Guard AI by RAADHANEX

This project is a real MVP foundation, not a fake certified audit platform. Features are either live, manual, needs API key, or not assessed.

## Accounts you need

| Account/service | Why needed | Required for public launch? |
|---|---|---|
| Supabase | Auth, DB, RLS, dashboard persistence | Yes |
| Razorpay | Real checkout, UPI/cards, subscriptions, webhook verification | Yes |
| UPI ID | Manual payment fallback | Yes |
| Vercel | Frontend hosting | Yes |
| Render/Railway/Fly | Backend hosting | Yes |
| Domain + DNS | Production URL + ownership verification | Yes |
| Lawyer/CA | Terms, privacy, refund, GST/compliance | Yes |
| Etherscan API | Verified contract address scanner | Recommended |
| GitHub token | Higher repo scan API rate limits | Recommended |
| OpenAI/Anthropic | Real AI fix assistant | Optional |
| RPC provider | Monitoring Lite | Optional |
| SMTP/Telegram/Discord/WhatsApp | Notifications | Optional |
| GoPlus | Wallet risk API | Optional |

## Backend-only secrets
Never put these in frontend env:
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `ETHERSCAN_API_KEY`
- `GITHUB_API_TOKEN`
- `SMTP_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `DISCORD_WEBHOOK_URL`
- `GOPLUS_ACCESS_TOKEN`

## What is still manual
- UPI manual payment verification unless Razorpay webhook verifies payment.
- Legal/CA review.
- Manual review delivery for paid audit packages.
- Deep audit tool installation and worker isolation.
- Production domain/DNS/SSL setup.
- Email/WhatsApp template approval.

## Real-only reminders
- Do not claim certified audit.
- Do not claim 100% secure.
- Do not show fake testimonials/client logos.
- Do not show fake monitoring/news/payment success.
- Do not collect private keys, seed phrases, or mnemonics.
