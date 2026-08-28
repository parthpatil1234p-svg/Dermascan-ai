# Deployment Guide

DermaScan AI is prepared for a college demonstration deployment. It is not a
medical-grade production system.

## Required Configuration

Create `backend/.env` from `backend/.env.example`. At minimum configure the
MongoDB URI/database, a random JWT secret of at least 32 characters, exact HTTPS
frontend origin, upload/storage limits, model paths, log level, and rate limits.
Set frontend `VITE_API_BASE_URL` at build time. Do not copy `.env` into images.

For a production-like environment:

```env
APP_ENV=production
JWT_SECRET_KEY=<random secret from a secret manager>
FRONTEND_ORIGIN=https://frontend.example
ENABLE_HSTS=true
AI_DEMO_MODE=false
```

Do not enable HSTS before HTTPS is correctly terminated. Multiple comma-separated
origins are accepted for known preview hosts; wildcard origins are rejected.

## Docker Compose

Docker Compose runs Nginx, FastAPI, and MongoDB with named database and temporary
storage volumes. The frontend proxies `/api` to the backend, avoiding a public
cross-origin API in the single-host layout.

```bash
cd dermascan-ai
copy deployment\.env.example .env
# Edit .env and replace JWT_SECRET_KEY.
docker compose build
docker compose up -d
docker compose ps
```

Unix-like systems use `cp deployment/.env.example .env`. Open
`http://localhost:5173`. Health is `/api/health`; readiness is `/api/readiness`.
Model files are mounted read-only from `backend/app/ml/models`. MongoDB persists
in `mongodb_data`; temporary image/PDF bytes use `temporary_storage`.

The backend container uses a non-root user and production Uvicorn workers. The
frontend uses a multi-stage npm build and unprivileged Nginx. A real deployment
should pin image digests and scan built images.

## Provider-Neutral Options

### Separate Services

Host the static frontend on Vercel or a similar service, FastAPI on Render or a
similar Python service, and MongoDB on Atlas. Configure the exact frontend URL in
CORS, private database network access, persistent temporary storage or object
storage, model artifact delivery, and an external cleanup schedule. Ephemeral
backend disks can delete temporary files before their metadata expires.

### One Virtual Machine

Run the supplied Docker Compose file behind a TLS reverse proxy. Back up MongoDB,
protect the host firewall, rotate secrets, monitor disk space, and schedule:

```bash
docker compose exec backend python -m app.scripts.cleanup_expired_data
```

### Managed Container Platform

Railway or a comparable platform can run the containers and Atlas. Confirm
persistent volumes, request body limits, cold-start/model memory, health probe
paths, and provider log-retention settings before relying on it.

## Production Verification

Verify HTTPS, CORS, health/readiness, registration/login, a consented upload,
model status, report/PDF creation, storage write access, cleanup, and absence of
secrets/personal data in logs. Record URLs only after they actually exist.

## Current Limitations

Rate limiting and metrics are process-local. JWT revocation, autoscaling-safe
temporary storage, managed secrets, centralized monitoring, alerting, backups,
and formal incident response remain deployment responsibilities.

