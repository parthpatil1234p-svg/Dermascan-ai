# API Reference

Base prefix: `/api`. Interactive OpenAPI is available at `/docs` while the
backend is running. Protected endpoints require `Authorization: Bearer <token>`.
Errors include `detail`, a stable broad `code`, and a request ID when available.

## Operations

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /health` | Public | Process health and model status |
| `GET /readiness` | Public | Database, catalogue, storage, model readiness |
| `POST /auth/register` | Public, limited | Create account and access token |
| `POST /auth/login` | Public, limited | Verify credentials and return token |
| `POST /auth/logout` | Public acknowledgement | Client removes stateless token |
| `GET /users/me` | User | Restore public account session |
| `GET/POST/PUT/DELETE /skin-profile` | User | Own self-reported profile |
| `GET /skin-profile/status` | User | Completion and next route |
| `POST /uploads/face-image` | Complete profile | Validate, sanitize, temporarily store |
| `GET/DELETE /uploads/{upload_id}` | Owner | Safe status or temporary deletion |
| `POST /image-quality/{upload_id}/analyze` | Owner and prerequisite | Technical quality report |
| `GET /image-quality/{upload_id}` | Owner | Existing quality report |
| `POST /image-quality/{upload_id}/accept-warning` | Owner | Explicit warning acceptance |
| `POST /face-detection/{upload_id}/analyze` | Owner and quality pass | One-face check and private crop |
| `GET /face-detection/{upload_id}` | Owner | Existing detection report |
| `POST /face-detection/{upload_id}/accept-warning` | Owner | Explicit warning acceptance |
| `POST /image-preprocessing/{upload_id}/process` | Owner and face pass | Model-input preparation |
| `GET /image-preprocessing/{upload_id}` | Owner | Existing preprocessing report |
| `POST /skin-type/{upload_id}/analyze` | Owner and preprocessing | Broad estimate or uncertainty |
| `GET /skin-type/{upload_id}` | Owner | Existing estimate |
| `GET /skin-type/model/status` | Public | Model contract readiness |
| `POST /skin-concerns/{upload_id}/analyze` | Owner and skin type | Visible observations |
| `GET /skin-concerns/{upload_id}` | Owner | Existing concern report |
| `GET /skin-concerns/model/status` | Public | Concern model readiness |
| `GET /products`, `GET /products/{id}` | Public | Paginated active catalogue |
| `GET /brands`, `GET /ingredients` | Public | Controlled catalogue metadata |
| `POST /product-eligibility/{upload_id}/evaluate` | Owner and analysis | Safety-first candidate filtering |
| `POST /product-recommendations/{upload_id}/generate` | Owner and eligibility | Rank eligible candidates only |
| `POST /skincare-routines/{upload_id}/generate` | Owner and recommendations | Deterministic morning/night routine |
| `POST /final-reports/{upload_id}/generate` | Owner and complete workflow | Versioned snapshot |
| `GET /final-reports`, `GET /final-reports/{id}` | Owner | History and report detail |
| `DELETE /final-reports/{id}` | Owner | Archive report |
| `POST /report-exports/{id}/export/pdf` | Owner, limited | Temporary PDF export |
| `POST/GET/PUT/DELETE /feedback` | User, owner | Submit, review, edit, withdraw |
| `/admin/*` | Admin | Catalogue and feedback review |

List endpoints document `page`, `page_size`, filters, and sorting in OpenAPI.
Ownership failures generally return safe `404` responses so another user's
resource existence is not disclosed. Rate limiting returns `429` with
`Retry-After`.

