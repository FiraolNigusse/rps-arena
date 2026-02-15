# RPS Arena – Deployment Guide

## Part 1 — Backend on Render

### Prerequisites

- Backend is prepared for production (see below)
- Render account

### Render setup

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your Git repo
3. **Root directory**: `backend`
4. **Build command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
5. **Start command**: `gunicorn core.wsgi` (or leave blank to use Procfile)
6. Add **PostgreSQL** in Render (or use external DB) and copy `DATABASE_URL`

### Environment variables (Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random secret (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DEBUG` | Yes | `False` for production |
| `ALLOWED_HOSTS` | Yes | `your-app-name.onrender.com` (Render provides the URL) |
| `DATABASE_URL` | Yes | Auto-set by Render if using their PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather |
| `JWT_SECRET_KEY` | Yes | Random secret for JWT |
| `CORS_ALLOWED_ORIGINS` | Yes | Frontend URL, **no trailing slash**, e.g. `https://rps-arena-virid.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Yes | Same as CORS, **no trailing slash** |

After deploy, set `ALLOWED_HOSTS` to your actual Render URL (e.g. `rps-arena-94pz.onrender.com`).

**Important:** For `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`, use the exact frontend URL **with no trailing slash** (e.g. `https://rps-arena-virid.vercel.app`). The backend now normalizes trailing slashes, but matching the browser’s Origin is more reliable without them.

### ⚠️ Stuck on "Initializing..." or "Connecting..."

- **Render cold start**: On the free tier, Render spins down the backend after ~15 min of no traffic. The first request can take **30–60 seconds**. The app will show "Connecting..." and, if it takes too long, "Server is slow to start. Tap to try again." Tap the screen to retry.
- If it never connects, check **Vercel** has `VITE_API_URL` set and you redeployed (see below).

### ⚠️ "Cannot reach server. Check CORS / API URL."

- **Vercel**: In Project → Settings → Environment Variables, add **`VITE_API_URL`** = `https://rps-arena-94pz.onrender.com/api` (use your real Render URL). Then **redeploy** (Deployments → ⋮ → Redeploy). Without this, the built app uses localhost and cannot reach the backend.

### ⚠️ "Authentication failed" after deployment

1. **CORS / Origin** – Add your **exact** Vercel URL to Render env vars (no trailing slash):
   - `CORS_ALLOWED_ORIGINS` = `https://rps-arena-xxxx.vercel.app`
   - `CSRF_TRUSTED_ORIGINS` = `https://rps-arena-xxxx.vercel.app`
   - Redeploy the Render service after changing these.

2. **Open from Telegram** – The app must be opened via your Telegram bot (Menu → Web App), not by pasting the Vercel URL in a browser.

3. **Multiple Vercel URLs** – If your bot opens a preview URL (e.g. `rps-arena-xxx-firaolnigusses-projects.vercel.app`), add that exact origin to `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` on Render as well (comma-separated), or point the bot’s Web App URL to your production domain only: `https://rps-arena-virid.vercel.app`.

4. **Vercel env** – Ensure `VITE_API_URL` is set in Vercel (e.g. `https://rps-arena-94pz.onrender.com/api`) and **redeploy** so the new build uses it.

5. **Telegram Bot** – In @BotFather, set your bot’s Web App URL to your production Vercel URL (e.g. `https://rps-arena-virid.vercel.app`).

### ⚠️ "Invalid Telegram data. Open from Telegram."

Shown when backend rejects `initData` (signature check fails). **Check Render logs** (Dashboard → your service → Logs) for one of:

- **"Telegram auth: no hash in initData"** – Frontend didn’t send hash; ensure the app is opened from the bot (Menu → Web App), not by opening the Vercel URL in a browser.
- **"Telegram auth: TELEGRAM_BOT_TOKEN not set"** – Set `TELEGRAM_BOT_TOKEN` in Render env exactly as in @BotFather (no extra spaces), then redeploy.
- **"Telegram auth: hash mismatch"** – Token may be wrong, or initData format differs. Confirm `TELEGRAM_BOT_TOKEN` is the token for the same bot whose Web App URL points to your Vercel app; redeploy backend after any env change.

The backend now tries both unquoted and raw value formats for the data-check string; if it still fails, the token is the most likely cause.

---

## Backend (Django)

### 1. Environment variables

Copy `backend/.env.example` to `backend/.env` and set:

- `SECRET_KEY` – random secret (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)
- `TELEGRAM_BOT_TOKEN` – from [@BotFather](https://t.me/BotFather)
- `JWT_SECRET_KEY` – random secret for JWT signing
- `DEBUG=False` in production
- `ALLOWED_HOSTS` – your domain(s), comma-separated
- `CORS_ALLOWED_ORIGINS` – frontend URL(s) when `DEBUG=False`

### 2. Database migrations

```bash
cd backend
python manage.py migrate
```

### 3. Static files (production)

```bash
python manage.py collectstatic --noinput
```

### 4. Run with Gunicorn (production)

```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

For ASGI (WebSockets):

```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

---

## Frontend (Vite/React)

### 1. Environment variables

Copy `frontend/.env.example` to `frontend/.env` and set:

- `VITE_API_URL` – backend API URL (e.g. `https://api.your-domain.com/api`)

### 2. Build

```bash
cd frontend
npm install
npm run build
```

Output is in `frontend/dist/`. Serve it with any static file server (Nginx, Vercel, Netlify, etc.) or from the same origin as the backend.

---

## Quick local development

```bash
# Terminal 1 – backend
cd backend && python manage.py runserver

# Terminal 2 – frontend
cd frontend && npm run dev
```

Ensure `frontend/.env` has `VITE_API_URL=http://127.0.0.1:8000/api`.
