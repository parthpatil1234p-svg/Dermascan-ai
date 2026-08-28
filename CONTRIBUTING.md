# Contributing

## Development Setup

1. Create `backend/.env` from `backend/.env.example` and use a local-only secret.
2. Create a Python 3.12 virtual environment and install
   `backend/requirements-dev.txt`.
3. Run MongoDB locally or with Docker.
4. Run `python -m app.scripts.seed_demo_data` from `backend`.
5. Install frontend dependencies with `npm ci` from `frontend`.

## Before A Change

- Keep route logic thin and ownership checks on the backend.
- Do not add real facial images, credentials, database dumps, unlicensed data,
  generated reports, or model files without a documented license and policy.
- Preserve cautious, non-diagnostic language and explicit uncertainty.
- Add tests proportional to the security and workflow impact.

## Required Checks

```bash
cd backend
ruff check app tests
black --check app tests
mypy app
pytest --cov=app

cd ../frontend
npm run lint
npm run test:coverage
npm run build
npm run test:e2e

cd ../ml
pytest
```

Document new environment variables, collections, endpoints, retention behavior,
and limitations in the same change.

