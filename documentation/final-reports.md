# Final Skin Guidance Reports

## Purpose And Safety Boundary

Step 14 creates an owner-scoped, reproducible snapshot from trusted backend reports. It separates self-reported profile information, technical image processing, AI-assisted visible observations, rule-based recommendation output, deterministic routines, and general safety guidance. The final report is not a medical diagnosis or prescription.

Raw facial images, storage paths, original filenames, device metadata, GPS data, face embeddings, landmark arrays, passwords, tokens, MongoDB identifiers, and hidden model implementation details are excluded from report responses and exports.

## Required Sources

The aggregator resolves the authenticated user's skin profile and owned upload, image-quality, face-detection, preprocessing, skin-type, visible-concern, product-recommendation, and skincare-routine reports. The product-eligibility report is retained as a trusted relationship source. The client supplies only a public upload ID.

Ownership, upload IDs, consent, public report links, recommendation-to-routine product membership, and model/engine version availability are validated before aggregation. Missing required modules create a clearly `incomplete` snapshot; inconsistent ownership or report relationships return a safe conflict response.

## Status And Versioning

- `complete`: all required sources are available without recorded workflow limitations.
- `complete_with_limitations`: usable with uncertainty, accepted warnings, catalogue limitations, stale information, demo products, or routine warnings.
- `incomplete`: at least one required source is unavailable and no missing value is inferred.
- `failed`: aggregation failed internally; this is not represented as an analysis limitation.
- `superseded`: a newer immutable version exists for the same upload.

Normal generation is idempotent for the same source fingerprint. Explicit regeneration creates the next integer version, inserts a new snapshot, preserves the prior document, and links `supersedes_report_id` and `superseded_by_report_id`. Public IDs use `DSR-{year}-{random token}` and do not encode email or private profile data.

## Report Sections

The report contains a header, prominent disclaimer, deterministic executive summary, user-provided profile summary, safe image-processing summary, estimated skin type and uncertainty, observed/possible/uncertain visible characteristics, controlled ingredient-role guidance, avoidance guidance, category-ranked product snapshots, morning and night routines, alternatives, safety instructions, dynamic limitations, model/engine transparency, and data-freshness dates.

Ingredient guidance uses fixed role and concern mappings plus saved allergy, avoidance, sensitivity, and fragrance preferences. It does not use a language model or invent ingredient claims. Executive summaries use deterministic templates populated only from stored evidence and explicitly preserve uncertainty.

## Product Snapshot Integrity

Each selected product snapshot stores only the displayed product ID, name, brand, category, rank, score, score band, explanation, cautions, price and check date, availability and check date, source verification date/status, and demo flag. Historical prices are labelled as values recorded when the report was generated. The full catalogue document is not copied.

## API

- `POST /api/skincare-routines/{upload_id}/generate`
- `GET /api/skincare-routines/{upload_id}`
- `POST /api/final-reports/{upload_id}/generate`
- `POST /api/final-reports/{upload_id}/regenerate`
- `GET /api/final-reports/by-upload/{upload_id}/latest`
- `GET /api/final-reports/{final_report_id}`
- `GET /api/final-reports` with owner-scoped pagination, status/date filters, and sorting
- `DELETE /api/final-reports/{final_report_id}` for soft archive
- `POST /api/final-reports/{final_report_id}/export/pdf`

Cross-user and missing report IDs both return `404`. Archived reports cannot be retrieved or exported through normal endpoints. Public sharing is not implemented.

## PDF And Print Privacy

PDFs are generated server-side from trusted report snapshots with ReportLab. Client HTML is never rendered. Storage names are random, paths remain private, responses use PDF/no-store headers, and successful downloads delete the temporary file after transfer. Startup cleanup removes abandoned expired `.pdf` and `.tmp` artifacts only after validating the configured export directory.

- `standard`: main profile, results, recommendations, routine, safety, and limitations.
- `privacy_reduced`: hides known allergies and detailed profile fields.
- `technical`: adds model/engine versions and data-freshness details.

All modes exclude the facial image. Every page has report ID, version, page number, and a non-diagnostic footer. The protected React print route uses the same API-owned snapshot and print CSS hides navigation and controls.

## Storage And Configuration

`final_skin_reports` uses a unique public report ID, a unique `(upload_id, report_version)` pair, an owner/date index, and status/archive indexes. `skincare_routine_reports` uses unique public report and upload IDs. Final snapshots use UTC timestamps and never overwrite history.

Configuration:

```env
REPORT_EXPORT_DIRECTORY=storage/temp_report_exports
REPORT_EXPORT_EXPIRY_MINUTES=30
REPORT_PDF_INCLUDE_PROFILE_DETAILS=true
REPORT_PDF_INCLUDE_TECHNICAL_DETAILS=false
```

## Testing And Limitations

Run `pytest` in `backend` and `npm run build` in `frontend`. Tests use deterministic fictional records and temporary export directories. They cover aggregation, ownership, relationships, missing sources, status rules, ingredient guidance, summaries, versioning, snapshots, history, archive, all PDF modes, escaping, random filenames, cleanup, and safe responses.

The catalogue remains fictional and availability is not real-time. Model-dependent stages still require legitimate exported model artifacts. A complete report reproduces the available workflow evidence; it cannot guarantee product safety, effectiveness, allergy safety, or clinical accuracy.

The final report provides general skincare guidance based on visible image characteristics, user-provided information, and the available product catalogue. It is not a medical diagnosis or prescription.
