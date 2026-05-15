# Deploy + Launch Pack — Web3Guard AI by RAADHANEX

## Backend on Render

1. Push project to GitHub.
2. Create a Render Web Service.
3. Use root directory: `backend`.
4. Runtime: Python 3.12.
5. Build command:

```bash
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

6. Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

7. Add env values:

```env
APP_ENV=production
FRONTEND_URL=https://your-vercel-domain.vercel.app
BACKEND_URL=https://your-render-service.onrender.com
ADMIN_TOKEN=replace_with_long_random_secret
RAADHANEX_UPI_ID=yourupi@bank
RAADHANEX_UPI_NAME=RAADHANEX
AI_ENABLED=false
AI_PROVIDER=none
AI_SEND_CODE=false
```

## Frontend on Vercel

1. Import the `frontend` folder.
2. Add env values:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
NEXT_PUBLIC_UPI_ID=yourupi@bank
NEXT_PUBLIC_UPI_NAME=RAADHANEX
NEXT_PUBLIC_PAYMENT_MODE=upi_manual
```

3. Deploy.
4. Open:

```text
/launch-pack
/local-qa
/scanner/unified-url
```

## Production QA checklist

- `/health` returns OK.
- `/health/readiness` has zero failures.
- `/launch/pack` returns deploy guidance.
- Frontend `/local-qa` loads.
- Unified URL scanner works on an authorized website.
- UPI intent opens correct UPI receiver.
- Lead form saves lead.
- Admin leads can be opened using `ADMIN_TOKEN`.
- CSV export works.
- Report preview print/save-as-PDF works.

## Public wording

Use:

> AI-assisted preliminary Web3 launch security review.

Do not use:

- Certified audit
- 100% secure
- Guaranteed exploit-free
- Payment successful without verification
- AI audited this project when AI is disabled
