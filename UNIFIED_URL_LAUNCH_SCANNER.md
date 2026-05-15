# Unified Website URL Launch Scanner

Endpoint:

```text
POST /scan/unified-url
```

Page:

```text
/scanner/unified-url
```

## Purpose

A Web3 founder often starts with only one public URL. This scanner creates a real launch-surface map from that URL and optional extra inputs without generating fake scores for missing modules.

## Input

```json
{
  "website_url": "https://project.example",
  "project_name": "Example Token",
  "project_type": "ERC20 / dApp",
  "chain": "Polygon",
  "contract_address": "0x... optional",
  "api_base_url": "https://api.project.example optional",
  "github_repo_url": "https://github.com/team/repo optional",
  "solidity_code": "optional pasted source",
  "authorization_confirmed": true,
  "real_only_acknowledged": true
}
```

## Real behavior

| Module | Behavior |
|---|---|
| Website | Live passive scan. |
| dApp | Live limited homepage hints only. No full source score from URL alone. |
| API | Live limited only if API URL is provided. |
| Contract | Live only if Solidity source is pasted. Contract address is recorded only for now. |
| Wallet | Manual input required. |
| Admin OpSec | Manual input required. |
| GitHub | Input recorded only until repo scanner phase. |

## Safety controls

- public http/https only
- private/internal IP blocking
- no exploit payloads
- no brute force
- no login bypass
- no credential testing
- HEAD/GET only for website passive checks
- authorization and real-only acknowledgement required

## Output highlights

- available partial score
- no full score unless all required modules are assessed
- module cards with Live / Manual / Input recorded only / Not assessed
- dApp hints from homepage HTML
- blocked fake claims
- next real inputs needed
