# DermaScan AI Backend

FastAPI backend for authentication, owner-scoped profiles and temporary images,
technical/AI-assisted analysis, catalogue eligibility, recommendations,
routines, versioned reports, PDF export, feedback, and Step 16 operational
hardening. It includes safe errors, request IDs, restricted CORS, process-local
rate limits, readiness checks, cleanup commands, and an explicit demonstration
mode.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Use `.venv\Scripts\activate.bat` in Command Prompt or `source .venv/bin/activate` on Unix-like systems. Set a strong `JWT_SECRET_KEY`, configure MongoDB, and install model artifacts only through the documented ML export workflow. OpenAPI docs are at `http://localhost:8000/docs`.

Health is available at `/api/health`. `/api/readiness` additionally checks the
database, product catalogue, private storage, and both model stages. It returns
`503` when real artifacts are unavailable. `AI_DEMO_MODE=true` enables only the
clearly labelled deterministic classroom fallback; it is disabled by default.

## Model Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SKIN_TYPE_MODEL_PATH` | `app/ml/models/skin_type_model.keras` | Local private model artifact |
| `SKIN_TYPE_MODEL_METADATA_PATH` | `app/ml/models/skin_type_model_metadata.json` | Exported contract/version metadata |
| `SKIN_TYPE_CLASS_MAP_PATH` | `app/ml/models/class_map.json` | Fixed output class map |
| `SKIN_TYPE_MIN_CONFIDENCE` | `0.60` | Minimum direct-class probability |
| `SKIN_TYPE_HIGH_CONFIDENCE` | `0.80` | High-confidence display threshold |
| `SKIN_TYPE_MIN_MARGIN` | `0.12` | Minimum top-versus-second separation |

The existing Step 7 variables define a `224 x 224 x 3` RGB, letterbox, `zero_to_one` model-input contract. Settings validation rejects invalid threshold ordering. The model loader rejects missing files, malformed metadata, unexpected class order, incompatible input/output shapes, and preprocessing-contract mismatches.

No production model binary is committed. Missing or incompatible artifacts produce a safe unavailable status and `503` inference response; the backend never substitutes random or static predictions.

### Visible Concern Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SKIN_CONCERN_MODEL_PATH` | `app/ml/models/skin_concern_model.keras` | Ten-output sigmoid model |
| `SKIN_CONCERN_MODEL_METADATA_PATH` | `app/ml/models/skin_concern_model_metadata.json` | Exported contract and version |
| `SKIN_CONCERN_LABEL_MAP_PATH` | `app/ml/models/skin_concern_label_map.json` | Fixed ten-label order |
| `SKIN_CONCERN_THRESHOLDS_PATH` | `app/ml/models/skin_concern_thresholds.json` | Validation-calibrated per-label thresholds |
| `CONCERN_UNCERTAINTY_MARGIN` | `0.05` | Borderline band around each threshold |
| `CONCERN_MODERATE_SEVERITY_DISTANCE` | `0.25` | Normalized prominence boundary |
| `CONCERN_PROMINENT_SEVERITY_DISTANCE` | `0.60` | Higher prominence boundary |

### Feedback Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `FEEDBACK_MAX_SUBMISSIONS_PER_HOUR` | `20` | Per-user submission limit |
| `FEEDBACK_DUPLICATE_WINDOW_SECONDS` | `60` | Identical-payload duplicate window |
| `FEEDBACK_MAX_COMMENT_LENGTH` | `1000` | Maximum free-text length |
| `FEEDBACK_ANALYTICS_MIN_GROUP_SIZE` | `3` | Minimum count before a grouped reason is emitted |

The concern loader rejects missing files, label-order drift, preprocessing mismatch, non-sigmoid metadata, incomplete dataset/evaluation identity, invalid thresholds, uncalibrated threshold sources, and input/output-shape mismatch. Development defaults may be used during experimentation, but they cannot enter runtime inference.

## Runtime Flow

1. Require JWT authentication and a complete skin profile.
2. Resolve the upload by public ID and authenticated owner.
3. Require completed or warning preprocessing and a private prepared image.
4. Acquire the startup-loaded model bundle.
5. Decode the private image to RGB, validate exact shape/variation, convert to `float32`, divide by 255 exactly once, and add one batch dimension.
6. Run prediction behind a process-local lock and validate `(1, 4)`, finite, non-negative output.
7. Normalize probabilities, map the saved class order, select top and second classes, calculate margin, and apply thresholds.
8. Compare oiliness and dryness transparently; keep self-reported sensitivity separate.
9. Upsert one report and update the upload to `skin_type_estimated` or `skin_type_uncertain`.

Unexpected inference failures return a generic message and `skin_type_analysis_failed`; no confident result is stored. Other unexpected failures restore the prior recoverable state.

## Fusion Rules

- Image confidence or margin below threshold: `Uncertain`, agreement `Insufficient`.
- Oily image + high oiliness/low-to-moderate dryness: strong agreement.
- Dry image + high dryness/low-to-moderate oiliness: strong agreement.
- Combination image + moderate/high values for both: strong agreement.
- Normal image + no high oiliness/dryness: strong agreement.
- Strong inverse questionnaire evidence: `Uncertain`, agreement `Conflict`.
- Other non-conflicting evidence: retain the model class with `Weak` agreement.
- Sensitivity never changes the four-class image output and is never diagnosed.

## Endpoints

- `POST /api/skin-type/{upload_id}/analyze`
- `GET /api/skin-type/{upload_id}`
- `GET /api/models/skin-type/status`
- `GET /api/health`
- `POST /api/skin-concerns/{upload_id}/analyze`
- `GET /api/skin-concerns/{upload_id}`
- `GET /api/models/skin-concerns/status`
- `GET /api/products` and `GET /api/products/{product_id}`
- `GET /api/brands`
- `GET /api/ingredients` and `GET /api/ingredients/{ingredient_id}`
- `POST|PUT|PATCH|DELETE /api/admin/products...` (admin only)
- `POST /api/product-eligibility/{upload_id}/evaluate`
- `GET /api/product-eligibility/{upload_id}`
- `GET /api/product-eligibility/{upload_id}/products/{product_id}`
- `POST /api/product-recommendations/{upload_id}/generate`
- `GET /api/product-recommendations/{upload_id}`
- `GET /api/product-recommendations/{upload_id}/products/{product_id}`
- `POST /api/skincare-routines/{upload_id}/generate` and `GET /api/skincare-routines/{upload_id}`
- `POST /api/final-reports/{upload_id}/generate` and `/regenerate`
- `GET /api/final-reports`, `/by-upload/{upload_id}/latest`, and `/{final_report_id}`
- `DELETE /api/final-reports/{final_report_id}`
- `POST /api/final-reports/{final_report_id}/export/pdf`
- `POST|GET /api/feedback`, `GET|PUT|DELETE /api/feedback/{feedback_id}`
- `GET /api/feedback/options`
- `GET /api/feedback/product-avoidance` and `DELETE /api/feedback/product-avoidance/{product_id}`
- `GET|PATCH /api/admin/feedback...` (admin only)
- `GET|PATCH /api/admin/catalogue-review-signals...` (admin only)

## Product Catalogue

Seed the controlled taxonomies, preview the 32-row fictional import, then import it:

```powershell
python -m app.scripts.seed_ingredients
python -m app.scripts.seed_brands
python -m app.scripts.import_products --file data/products/demo_products.json --dry-run
python -m app.scripts.import_products --file data/products/demo_products.json
```

`PRODUCT_PRICE_STALE_DAYS=30`, `PRODUCT_AVAILABILITY_STALE_DAYS=14`, and `PRODUCT_SOURCE_VERIFICATION_STALE_DAYS=90` control public freshness warnings. Product IDs/slugs, ingredient names, and brand names are unique. Public APIs exclude inactive and unverified-draft records. Registration never grants catalogue administration; `is_admin` must be assigned through trusted database operations. Full schema, filter, import, index, and safety documentation is in `../documentation/product-catalogue.md`.

`BUDGET_SOFT_OVERAGE_PERCENT=10` controls the caution tolerance when the filtering context uses a flexible budget. A profile with explicit minimum and maximum values is treated as strict by the current MVP. Allergy aliases and avoided ingredients are normalized against the controlled taxonomy; exact identifiers and explicit categories are used instead of substring matching. Unknown critical data produces `insufficient_information`. Full policy and reason-code documentation is in `../documentation/product-eligibility.md`.

Analysis and report retrieval require authentication, ownership, profile completion, and preprocessing. Cross-user and missing IDs return `404`; prerequisites return `409`; missing private files return `410`; unavailable models return `503`; internal inference errors return a safe `500`. Responses never contain model paths or image references.

## MongoDB

Step 15 adds `user_feedback`, `user_product_avoidance`, `recommendation_improvement_signals`, `catalogue_review_signals`, `feedback_analytics_snapshots`, and `feedback_moderation_audit`. Public feedback IDs are random `FDB-...` values. User IDs are always derived from JWT authentication, related reports/products are ownership-checked, comments are escaped and length-limited, and aggregate snapshots omit identifiers and raw comments. Catalogue feedback creates review signals only; catalogue records are never updated automatically.

`skin_type_reports` uses unique indexes on `skin_type_report_id` and `upload_id`, plus an owner index. A report stores owner, workflow references, model name/version, top and second predictions, full-precision probabilities, margin, questionnaire evidence, sensitivity, agreement, final result, issues, and UTC timestamps. Re-analysis updates the same report and preserves its public ID and creation time.

Parent upload deletion and expiry cleanup remove the report alongside private image derivatives. The report contains no bytes, paths, credentials, protected attributes, identity data, or medical conclusions.

`skin_concern_reports` has unique indexes on `skin_concern_report_id` and `upload_id`, plus an owner index. It stores full-precision internal scores and thresholds, interpreted label status/prominence, questionnaire comparison, honest region availability, model version, prerequisite report IDs, limitations, and UTC timestamps. Re-analysis updates the existing record. Public output contains only observed/possible labels and a separate uncertain list.

`product_eligibility_reports` has unique indexes on `eligibility_report_id` and `upload_id`, plus an owner index. Each record stores prerequisite report IDs, catalogue and engine versions, the normalized filtering context, compact per-product decisions and reasons, counts, and UTC timestamps. Re-evaluation updates the same report. It stores no image data, path, password, token, or recommendation score.

`product_recommendation_reports` has unique indexes on `recommendation_report_id` and `upload_id`, plus an owner index. It stores owner and prerequisite IDs, catalogue/scoring versions, the validated weight/penalty snapshot, compact candidate results, selected category recommendations, confidence, limitations, and UTC timestamps. Regeneration updates one report per upload and preserves excluded candidate boundaries. Full scoring documentation is in `../documentation/product-recommendations.md`.

`skincare_routine_reports` stores one owner-scoped deterministic morning/night routine per upload. `final_skin_reports` preserves immutable integer versions with unique public IDs, public source-report relationships, safe product price/availability snapshots, report sections, freshness, limitations, export status, supersession links, archive state, and UTC timestamps. See `../documentation/final-reports.md`.

Concern analysis requires an owned unexpired upload, complete profile, completed/warning preprocessing, successful or uncertain skin-type report, an unexpired private derivative with the exact exported input shape, and a loaded validated concern model. Ownership violations and missing IDs both return `404`; prerequisites return `409`; missing or expired files return `410`; unavailable models return `503`; inference failures return a generic `500`.

## Tests

```powershell
ruff check app tests
black --check app tests
mypy
pytest --cov=app
pip-audit -r requirements.txt
```

The recommendation suites cover component boundaries, exact weighting, penalty caps, score bands, stable ties, category/diversity rules, explanations, confidence, authentication, ownership, prerequisites, candidate isolation, report upsert, pagination, safe details, and workflow status. All fixtures are isolated and use no personal data.

## Limitations

- TensorFlow and a trained `.keras` artifact are required for live inference.
- The current lock protects model prediction inside one process; production multi-worker deployment needs load and memory planning.
- Local private derivatives and startup cleanup are college-MVP infrastructure.
- Confidence calibration and fairness depend on the future representative test dataset.
- Recommendation and routine logic are deterministic project-specific guidance, not medical suitability, prescription, or guaranteed effectiveness. Public sharing and permanent PDF URLs are not implemented.
- No trained concern artifact or performance claim is bundled; the live concern endpoint remains unavailable until legitimate export.
- Current concern inference is global and cannot provide validated fine-grained localization.
- Mypy currently gates the new hardening modules incrementally; legacy domain
  modules still contain strict-typing debt.
- Rate limiting and metrics are process-local, and temporary storage is not
  suitable for a horizontally scaled deployment.

Skin-type output is a broad skincare-oriented estimate. It does not diagnose skin disease or replace a qualified dermatologist.
