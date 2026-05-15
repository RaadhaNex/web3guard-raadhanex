# Phase 15 — Real AI Fix Assistant

## What is live

Phase 15 adds a real, backend-only AI Fix Assistant foundation:

- `GET /ai/fix-assistant/status`
- `POST /ai/fix-assistant/suggest`
- Frontend page: `/ai-fix-assistant`
- Safe local fallback fix guidance when no provider is configured
- Optional OpenAI / Anthropic provider mode
- Code privacy gates before any code context can be sent
- Secret-like value redaction before provider calls
- Suggested patch direction, snippets/diffs, tests, validation steps, and manual-review notes

## Real-only rules

The assistant never claims:

- guaranteed fix
- certified audit
- automatic production code modification
- exploit generation
- private key or seed phrase collection

`auto_apply_allowed` is always `false` in Phase 15.

## Backend environment

Fallback mode, no provider call:

```env
AI_ENABLED=false
AI_PROVIDER=none
AI_FIX_ENABLED=false
AI_SEND_CODE=false
AI_FIX_SEND_CODE=false
```

OpenAI provider mode:

```env
AI_ENABLED=true
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-real-key
AI_MODEL=gpt-4o-mini
AI_FIX_ENABLED=true
AI_SEND_CODE=false
AI_FIX_SEND_CODE=false
```

Anthropic provider mode:

```env
AI_ENABLED=true
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-real-key
ANTHROPIC_MODEL=claude-3-5-haiku-latest
AI_FIX_ENABLED=true
AI_SEND_CODE=false
AI_FIX_SEND_CODE=false
```

Code context is **not sent** unless all of these are true:

```env
AI_ENABLED=true
AI_FIX_ENABLED=true
AI_SEND_CODE=true
AI_FIX_SEND_CODE=true
```

and the request includes:

```json
{
  "include_code": true,
  "privacy_acknowledged": true
}
```

## Manual account setup

To use real AI provider mode you need one of these accounts:

- OpenAI Platform account + API key
- Anthropic Console account + API key

Keys stay backend-only. Never put provider keys into `frontend/.env.local`.

## Current limitation

The assistant generates suggestions only. It does not write files, open PRs, or auto-apply patches. A later phase can add an approved patch/PR workflow.
