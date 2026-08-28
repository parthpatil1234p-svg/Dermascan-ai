# Testing Strategy

## Test Layers

- Backend unit/service tests cover validation, image metrics, scoring, filters,
  routines, privacy, model contracts, and report assembly.
- Backend API/authorization tests use fake isolated collections and temporary
  directories; they do not connect to production data.
- ML tests cover datasets, preprocessing, model shape, thresholds, metrics, and
  concern pipeline contracts without requiring a production model.
- Frontend Vitest tests cover validation, shared states, and route prerequisite
  declarations with deterministic browser APIs.
- Playwright tests run real Chromium against Vite for the application shell,
  protected-route redirect, client-side login validation, and desktop/mobile
  overflow checks.

## Commands

```bash
cd backend
ruff check app tests
black --check app tests
mypy
pytest --cov=app --cov-report=term-missing --cov-report=html

cd ../frontend
npm ci
npm run lint
npm run test:coverage
npm run build
npx playwright install chromium
npm run test:e2e

cd ../ml
pytest
```

## Critical Safety Coverage

Authentication tests cover registration, duplicate email, password hashing,
generic invalid credentials, inactive users, missing/invalid/expired tokens, and
protected current-user reads. Ownership tests use at least two users for upload,
analysis, catalogue workflow, final report, and feedback records.

Image tests generate non-personal synthetic arrays and files for valid JPEG/PNG,
fake extensions, MIME mismatch, corruption, size/dimension limits, blur,
brightness, exposure, contrast, no face, multiple faces, expiry, missing files,
path confinement, metadata removal, and cleanup.

Recommendation tests assert that allergy, avoided ingredient, geography,
availability, age caution, and user-product-avoidance exclusions never re-enter
ranking or routines. Uncertain model output remains uncertain.

## E2E Scenarios

The committed Playwright suite covers the real unauthenticated application
boundary and responsive shell. The complete model-dependent workflow must be
run against either valid trained artifacts or explicit `AI_DEMO_MODE=true`; it
is not falsely passed when artifacts are absent. Manual scripts in
`demo-guide.md` cover valid upload, invalid format, blurry image, no-face image,
strict exclusion, uncertain output, no eligible products, PDF, feedback, and
cross-user access.

## Coverage Policy

Coverage is evidence, not a substitute for assertions. The target is at least
80% backend overall where practical and stronger coverage for authentication,
ownership, upload validation, eligibility, and feedback privacy. Frontend
coverage is targeted at critical workflow code; a lower overall percentage is
expected while visual pages remain integration-tested. Actual measured values
belong in `final-readiness-report.md` and must be updated only after execution.

## Test Isolation

Tests set `APP_ENV=testing`, use fake collections or a test database, and use
pytest temporary directories. Never point tests at a production URI. Playwright
creates no account because its committed smoke paths stop before API submission.

## Verified Baseline

On 2026-08-08, the patched Python 3.12 stack completed 495 backend tests with
87.44% line coverage and 72.29% branch coverage. The ML workspace completed 38
synthetic-fixture tests. Frontend Vitest completed 7 tests and Playwright
completed 8 checks across desktop Chromium and Pixel 5. Full frontend source
coverage is currently only 2.93% by lines, so expanding component, context, and
workflow integration coverage remains a high-priority engineering task.

Mypy is an incremental gate over the six new hardening modules listed in
`backend/pyproject.toml`. A whole-application strict run currently reports
legacy typing debt and is not represented as clean.
