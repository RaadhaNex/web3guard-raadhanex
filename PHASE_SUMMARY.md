# Web3Guard AI v3.1 — Report Realism + Direct Export UX Patch

## What changed

This patch improves the report/PDF flow after the v3 advanced scanner update.

### 1. Direct export from URL scanner result
- After a user runs the Unified URL Scanner, the same page now shows a **Report & exports** section.
- User no longer needs to go through Dashboard → Scans → Create Report → Export.
- Export options are available directly from the scan result:
  - PDF
  - HTML
  - Markdown
  - JSON
- Dashboard save still remains available for persistence/history.

### 2. Real bugs + fix hints in report
- PDF/HTML reports now separate:
  - Real bugs/findings with fix hints
  - Evidence required / Not assessed modules
  - Evidence summary
  - Module matrix
  - Priority action plan
- Missing input is no longer mixed into Top Findings as if it was a real bug.
- Missing input appears under Evidence Required / Not assessed modules.

### 3. Better PDF realism
- Score label now distinguishes partial assessed-surface score from full launch score.
- The report still blocks fake audit language.
- Report keeps real-only wording:
  - Missing modules remain Not assessed.
  - Not a certified audit.
  - No fake full score.

### 4. Code editor option on scanner page
- Added top-right Code Editor toggle on the Unified URL Scanner page.
- User can paste/edit Solidity source in a VS Code-style editor area before running the scan.
- No code execution is performed. It only sends pasted source to the passive/rule-based scanner.

## Changed files
- backend/app/services/professional_report.py
- backend/app/services/dashboard_report_export.py
- frontend/components/scanner/UnifiedUrlScannerClient.tsx

## Tests run in sandbox
- `python -m pytest tests/test_phase9_professional_reports.py -q` → 3 passed
- Direct sample PDF generation using `build_pdf_bytes()` passed and produced real PDF bytes.

Full backend pytest in this reconstructed sandbox still shows unrelated existing phase/status assertion failures that are not caused by this patch. The report-specific tests pass.

## Apply rule
Apply after v3 advanced patch. Replace only the files in this ZIP. Do not overwrite env files, data files, Supabase secrets, Render env, Vercel env, or production database.
