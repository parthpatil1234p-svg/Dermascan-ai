# Final Readiness Report

Date: 2026-08-08

## Verdict

DermaScan AI is ready for a supervised local college demonstration with either
legitimate exported models or the explicit `AI_DEMO_MODE=true` fallback. It is
not production-ready or clinically validated. Real model mode correctly reports
not ready because no trained model artifacts are committed. No deployment was
performed, and Docker could not be built because Docker is not installed on the
verification machine.

## Verification Environment

- Windows, Python 3.12.13, Node.js 24.19.0, npm 11.17.0.
- MongoDB Windows service running locally.
- Frontend checked with Chromium 151 through Playwright desktop and Pixel 5
  projects, plus a separate in-app browser inspection.
- Test data used fake collections, generated arrays/files, and a synthetic
  non-personal portrait. No real facial photograph was used.

## Automated Results

| Gate | Result |
| --- | --- |
| Backend pytest | 495 passed in 97.90 seconds with coverage, no warnings |
| Backend coverage | 87.44% lines, 72.29% branches, 84.6% combined display |
| ML workspace pytest | 38 passed in 19.49 seconds, no warnings |
| Frontend Vitest | 7 passed |
| Frontend Playwright | 8 passed across desktop and mobile |
| Frontend ESLint | Passed with zero warnings |
| Ruff | Passed for `app` and `tests` |
| Black | 208 files unchanged in final check |
| Mypy | Passed for 6 scoped hardening modules |
| Frontend production build | Passed, 1,744 modules transformed |
| npm audit | No known vulnerabilities |
| pip-audit | No known vulnerabilities in production requirements |
| YAML parse | Compose and all three GitHub workflows parsed successfully |

Frontend all-source coverage is 2.93% lines, 2.64% statements, 0.50% branches,
and 0.78% functions. The unit suite is deliberately small and is supplemented
by browser tests, but this remains an important coverage gap.

## Live API Checks

Real model mode on `127.0.0.1:8001`:

- `/api/health`: `200`, database-independent liveness, model artifacts unavailable.
- `/api/readiness`: `503`, database/catalogue/storage ready, both models not ready.
- `/openapi.json`: `200`, API version `0.16.0`.
- Responses included `X-Request-ID` and `X-Content-Type-Options: nosniff`.

Explicit demonstration mode on `127.0.0.1:8002`:

- `/api/health`: `200`, both deterministic demo bundles labelled `demonstration`.
- `/api/readiness`: `200`, analysis mode labelled `demonstration`.

An isolated demonstration-mode API walkthrough used a generated synthetic
portrait and a dedicated temporary database. Registration, session retrieval,
profile creation, consented upload, quality analysis, face detection,
preprocessing, skin-type and visible-concern demo analysis, catalogue
eligibility, recommendation ranking, routine generation, final report detail,
privacy-reduced PDF export, and feedback all returned successful responses. The
PDF began with a valid `%PDF-` signature. The catalogue evaluated 32 fictional
products, retained 25 with cautions, and ranked 7 for display. The owned-upload
cleanup path removed image-bearing records and files; the isolated database was
then dropped and confirmed absent.

This walkthrough exposed and fixed a compatibility defect in which
`mediapipe==0.10.35` lacks the legacy `mp.solutions` namespace. The adapter now
detects that package shape and uses the existing OpenCV Haar fallback, covered
by a regression test. The same synthetic upload then produced one centred face
and a private 944 x 944 crop.

These checks prove startup and readiness behavior. They do not prove a remote
deployment, clinical validity, or trained-model accuracy.

## Local Performance Sample

Twenty-five sequential PowerShell HTTP requests were measured on the local
development machine, with no concurrency or warm-up exclusion:

| Endpoint | Mean | p50 | p95 |
| --- | ---: | ---: | ---: |
| `/api/health` | 63.58 ms | 35.50 ms | 120.56 ms |
| `/api/readiness` | 24.44 ms | 23.71 ms | 26.56 ms |

The final production build completed in 9.33 seconds. Its shared JavaScript entry was
303.34 kB (96.73 kB gzip), CSS was 31.88 kB (6.15 kB gzip), and the hero PNG was
1,355.28 kB. These local observations are not load-test or production SLO data.
No model-inference latency was measured because real artifacts are absent.

## Security And Privacy Audit

- Production/staging configuration rejects weak placeholder JWT secrets and
  wildcard/invalid frontend origins.
- Passwords use Argon2; unknown-email login performs a dummy hash check; login
  errors remain generic.
- JWTs contain only required identity/time claims and are not logged.
- Backend ownership tests cover private uploads, reports, recommendations, and
  feedback; frontend guards are not treated as authorization.
- Uploads validate extension, claimed MIME, decoded content, size, dimensions,
  decompression risk, orientation, and metadata removal before private storage.
- Safe errors carry stable codes and request IDs without paths, stack traces,
  tokens, profile answers, comments, or image bytes.
- Route-class rate limits are enabled, but are process-local and therefore not
  a distributed production control.
- The browser stores the access token in `localStorage` and the public active
  upload ID in `sessionStorage`. This leaves an acknowledged XSS/token-theft
  tradeoff; no password, raw image, allergy list, or report is stored there.
- Temporary uploads, crops, prepared images, and PDFs have cleanup support.
  Report deletion is archival, and account erasure/data export are not present.

## Medical-Language Audit

The final safety disclaimer is centralized in frontend constants and included
in report output. A repository search found no dermatologist-equivalence,
clinical-proof, diagnosis-result, or guaranteed-accuracy claim. One match for
"guaranteed results" appears only inside a product limitation that explicitly
denies such a guarantee.

## Deployment And CI

The repository contains backend/frontend Dockerfiles, Compose, unprivileged
Nginx configuration, deployment environment examples, health checks, persistent
MongoDB and temporary-storage volumes, and backend/frontend/security GitHub
Actions workflows. Docker is unavailable on this machine, so image build,
Compose startup, container health, HTTPS, remote CORS, and a deployed URL remain
unverified. No deployment success is claimed.

## Remaining Risks

1. No licensed representative dataset, trained artifacts, calibrated real-world
   thresholds, accuracy, fairness evaluation, or clinical validation exists.
2. The full browser workflow was not run against real models. The complete API
   workflow passed only in explicit demonstration mode, which is a deterministic
   workflow aid and not AI evidence.
3. Frontend unit coverage is low, and whole-backend strict mypy still has legacy
   typing debt outside the scoped six-module gate.
4. Access tokens are not revocable and are stored in `localStorage`.
5. Rate limits/metrics are process-local; storage is host-local; no centralized
   monitoring, alerting, backup verification, or incident automation exists.
6. Docker and remote deployment verification remain outstanding.
7. The 1.35 MB hero image could be further optimized.

## Final Safety Disclaimer

DermaScan AI provides general skincare guidance based on visible facial
characteristics and user-provided information. It is not a medical diagnostic
system, does not prescribe treatment, and does not replace advice from a
qualified dermatologist.

Users experiencing severe, painful, infected, persistent, rapidly changing, or
unusual skin concerns should seek advice from a qualified healthcare professional.
