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
| `CORS_ALLOWED_ORIGINS` | Yes | Frontend URL, e.g. `https://your-app.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Yes | Same as CORS, e.g. `https://your-app.vercel.app` |

After deploy, set `ALLOWED_HOSTS` to your actual Render URL (e.g. `rps-arena-api.onrender.com`).

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
