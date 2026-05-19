# Responsible Disclosure Workflow

Sentinel can generate disclosure drafts, but it does not send them automatically.

## Safe workflow
1. Sentinel generates a candidate alert from stored records.
2. Admin validates scope, authorization, and evidence quality.
3. Admin finds official contact via `security.txt`, SECURITY.md, or official website.
4. Admin sends a respectful disclosure manually.
5. Admin tracks status outside public marketing claims until confirmed.

## Draft statuses
- `draft_only_not_sent`
- `sent_manual`
- `acknowledged`
- `fixed`
- `closed`
- `no_response`

## Rules
- No exploit attempts.
- No coercive sales copy.
- No private key or seed phrase requests.
- No wallet signing.
- No public shaming before validation.
- No “hacked” claim unless independently verified.
