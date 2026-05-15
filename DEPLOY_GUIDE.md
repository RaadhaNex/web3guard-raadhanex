# Deploy Guide

## Backend on Render

- Runtime: Python 3.12
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set env variables from `.env.example`

## Frontend on Vercel

- Root: `frontend`
- Install command: `npm install`
- Build command: `npm run build`
- Env:
  - `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`
  - `NEXT_PUBLIC_UPI_ID=yourupi@bank`
  - `NEXT_PUBLIC_UPI_NAME=RAADHANEX`

## UPI

Use real UPI ID before production. In future, add Razorpay Checkout and webhook verification.
