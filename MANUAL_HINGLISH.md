# Web3Guard AI by RAADHANEX — Hinglish Manual

## Phase 3 me kya add hua?
Is phase me scanner ke result se ek proper **Launch Readiness Report** generate hota hai.

AI optional hai. Agar tum AI key nahi doge to app fake AI output nahi dikhayega. Uski jagah safe local fallback explanation use hogi.

## Kaise use kare?
1. Backend run karo.
2. Frontend run karo.
3. `/scanner/contract` open karo.
4. Sample contract load karo ya apna Solidity code paste karo.
5. `Run Preliminary Review` click karo.
6. Result aane ke baad `Generate Report` click karo.
7. Report preview aayega.
8. `Print / Save as PDF` se client ko PDF de sakte ho.

## Important baat
Ye certified audit nahi hai. Isko pre-audit readiness report ke roop me use karo.

## AI ka sach
- `AI_ENABLED=false` hai to fallback explanation chalegi.
- AI key backend me hi rakho.
- Frontend me kabhi AI key mat daalna.
- `AI_SEND_CODE=false` recommended hai, warna privacy policy aur user consent chahiye.

## Payment
UPI payment CTA Phase 1 se ready hai. Phase 4 me income funnel aur admin lead workflow aur strong hoga.


## Phase 5.8 — Final Report ka use kaise karein

1. Scanner module run karo.
2. Result aane ke baad **Generate Final Report** click karo.
3. Agar sirf ek module scan hua hai to report partial score dikhayegi.
4. Full launch score ke liye 6 modules complete karo:
   - Contract
   - Website
   - dApp
   - API
   - Wallet
   - Admin OpSec
5. Report ko Markdown/JSON me download kar sakte ho.
6. PDF ke liye **Print / Save PDF** button use karo.

Public me kabhi bhi “certified audit” mat likhna. Safe wording:

> Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX
