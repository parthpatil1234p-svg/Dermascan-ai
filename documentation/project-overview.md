# Project Overview

## Problem Statement

A facial image may contain broad visible characteristics associated with skin behavior, but image-only classification is uncertain, affected by capture conditions, and cannot reliably determine sensitivity or diagnose disease. A responsible college project needs a reproducible training pipeline, explicit model contract, conservative uncertainty, transparent questionnaire comparison, strict ownership, and honest limitations.

## Step 8 Through Step 16 Solution

DermaScan AI now provides the engineering foundation for a MobileNetV2 classifier with exactly four image classes: `normal`, `oily`, `dry`, and `combination`. The backend can load a legitimate exported model once, run it only against the authenticated user’s private Step 7 derivative, validate probabilities, combine the image estimate transparently with self-reported oiliness/dryness, keep sensitivity separate, store an owned report, and return `Uncertain` when evidence is weak or conflicts.

Step 9 extends that foundation with ten independent visible skin-characteristic labels, masked multi-label training, validation-calibrated thresholds, uncertainty bands, image-prominence wording, relevant questionnaire comparison, honest full-face fallback, owned report storage, and a real frontend report.

Step 10 adds a separate structured catalogue foundation: controlled product, brand, and ingredient records; exact alias normalization; dated INR price and India availability snapshots; safe search/filter APIs; protected administration; deterministic imports; and public discovery interfaces. The included records are clearly fictional. Catalogue matches are not personalized recommendations, medical suitability decisions, or allergy guarantees.

Step 11 applies strict owner-scoped eligibility rules. Step 12 ranks only the surviving eligible and caution candidates using versioned component weights, bounded caution penalties, independent confidence, category limits, deterministic diversity, and evidence-based explanations. Excluded and insufficient-information products cannot be scored or restored.

Step 13 orders only those recommendations into cautious morning/night routines. Step 14 validates every trusted source relationship and preserves a versioned final snapshot with separated evidence sources, product price/availability snapshots, deterministic ingredient guidance and summary text, owner-scoped history, print layout, and private PDF export.

Step 15 collects optional structured feedback against owned report-time snapshots. It preserves user edits and withdrawals, separates analytics and academic-review consent, creates private per-user avoidance preferences after an explicit choice, and creates non-public catalogue-review signals without changing catalogue facts or retraining AI models.

Step 16 hardens the complete system with consistent safe errors, request IDs,
security headers, restricted CORS, process-local rate limiting, dependency
audits, route code splitting, browser tests, readiness checks, cleanup commands,
container definitions, CI workflows, privacy/security policies, fictional seed
data, and an explicit deterministic demonstration mode. Real model mode still
fails closed when compatible artifacts are absent.

No dataset or trained model is bundled. Live inference remains unavailable until a licensed dataset is validated, models are genuinely trained and evaluated, and compatible artifacts are exported. No performance metric is fabricated.

## Target Users

- College assessors reviewing a complete and responsible full-stack ML workflow.
- Students demonstrating reproducible dataset, training, evaluation, API, and UI practices.
- Future skincare users seeking broad general guidance, not diagnosis.

## Workflow

1. Authenticate and require a complete skin profile.
2. Require owned upload, passed/accepted quality and face stages, and completed preprocessing.
3. Resolve the private `224 x 224 x 3` RGB derivative without accepting a client path.
4. Confirm model, metadata, class map, shape, channel order, normalization, and resize contract.
5. Convert once to `float32` in range 0–1 and create a batch tensor.
6. Run the four-output model and validate finite non-negative probabilities.
7. Select top/second classes and calculate confidence margin.
8. Return `Uncertain` below confidence or margin thresholds.
9. Compare the image estimate with self-reported oiliness and dryness without rewriting probabilities.
10. Display sensitivity separately and disclose disagreement.
11. Upsert one owned `skin_type_reports` document and show the real API result.
12. Require a valid skin-type report before concern analysis.
13. Run a ten-output sigmoid model and validate every finite score in range 0-1.
14. Apply validation-calibrated label thresholds and preserve a configurable uncertainty band.
15. Compare only visible oiliness and dry-looking labels with corresponding self-reports.
16. Keep sensitivity, allergies, and redness logically separate.
17. Upsert one owned `skin_concern_reports` document and show observed/possible and uncertain lists separately.
18. Continue to protected catalogue discovery after the concern report.
19. Search only active public records with validated URL filters and pagination.
20. Keep private profile, allergy, and analysis data out of catalogue URLs.
21. Evaluate every catalogue record with immutable Step 11 exclusions and cautious missing-data handling.
22. Score only eligible and caution candidates with the saved profile, analysis evidence, and catalogue data.
23. Apply category-aware selection, deterministic diversity, and stable tie breaking.
24. Show component scores, penalties, confidence, evidence, cautions, and limitations.
25. Generate deterministic morning/night steps without restoring excluded products.
26. Validate source ownership and report relationships before final aggregation.
27. Preserve immutable final-report versions, product snapshots, safety guidance, and limitations.
28. Provide protected detail, history, print, archive, and private PDF export workflows.
29. Link optional feedback to the authenticated user's immutable report, recommendation, routine, or product snapshot.
30. Validate controlled ratings/reasons, sanitize text, and support editing and withdrawal.
31. Use consented active feedback for identifier-free aggregates and keep moderation/admin actions protected.
32. Apply active user product avoidance only to that user's future eligibility results.

## Dataset Governance

Each manifest row requires an image ID, safe relative path, one supported label, documented source/license, subject ID, split, dimensions, quality status, and notes. Application user uploads are excluded unless users separately and explicitly consent to model training; ordinary analysis consent is insufficient.

Validation checks missing/invalid labels, source/license, unsafe or duplicate paths, unsupported formats, unreadable/corrupt files, exact hash duplicates, potential perceptual duplicates, class and size distribution, and subject leakage. Subject-level fixed-seed splitting groups classes where practical into 70% training, 15% validation, and 15% untouched testing. When subject IDs are unavailable, leakage risk must be documented rather than hidden.

Dataset review should consider skin-tone, age, lighting, camera, gender, facial appearance, and geographic coverage where ethically collected metadata permits. DermaScan AI does not classify those attributes. Missing representative metadata prevents a complete fairness evaluation.

## Training And Augmentation

MobileNetV2 was chosen for a lightweight CPU-oriented MVP. The architecture uses an ImageNet convolutional base, global average pooling, dropout, and four-class softmax output.

- Stage 1 freezes the base and trains the head with validation-loss early stopping.
- Stage 2 unfreezes a configured number of upper layers, keeps batch normalization frozen, and uses a smaller learning rate.
- Best validation checkpoints, learning-rate reduction, CSV history, and TensorBoard logging are configured.
- Class weights compensate for training imbalance.
- Training-only transformations are small horizontal flip, rotation, translation, zoom, brightness, and contrast changes.
- Validation and test inputs receive no random augmentation.

The input contract is RGB `224 x 224 x 3`, letterbox resize, `float32`, and exactly one division by 255.

## Evaluation And Calibration

The untouched test pipeline writes accuracy, macro precision/recall/F1, weighted F1, per-class precision/recall/F1/support, cross-entropy, confusion matrix, confidence distribution, expected calibration error, reliability diagram, confidence histogram, training curves, classification report, model metrics, and an evaluation report with dataset/split/training/fairness limitations.

Actual values remain absent until a real dataset and trained checkpoint exist. Softmax output is not automatically calibrated; `0.60` direct confidence, `0.80` high confidence, and `0.12` top-two margin are conservative initial settings to tune from real evaluation.

## Questionnaire Fusion

- Strong agreement returns the image class and explains the consistency.
- Weak non-conflicting evidence returns the image class with weak agreement.
- Low image confidence or margin returns `Uncertain`.
- Strongly inverse oiliness/dryness evidence returns `Uncertain` with visible conflict.
- Original probabilities remain unchanged.
- Self-reported sensitivity is displayed as `Yes`, `No`, or `Not sure`; it never becomes an image class or medical conclusion.

Current routine and notes remain stored in the profile for later recommendation context. They are not parsed as hidden medical evidence in this initial fusion rule set.

## Model Artifacts And Loading

The export workflow requires a real best `.keras` checkpoint and real evaluation metrics. It creates `skin_type_model.keras`, `skin_type_model_metadata.json`, `class_map.json`, and `model_metrics.json` under the private backend model directory. The metadata records architecture, input contract, class order, training date, dataset version, and actual metrics only.

At startup, the registry loads the bundle once and records a safe readiness reason. Missing TensorFlow/files, invalid JSON, fixed-class mismatch, input/output-shape mismatch, or preprocessing mismatch prevents readiness. Health and model-status responses contain no physical paths.

The concern export adds `skin_concern_model.keras`, contract/version metadata, the fixed label map, calibrated per-label thresholds, and real evaluation metrics. Its registry also checks sigmoid output metadata, exact ten-label order, validation threshold provenance, dataset/evaluation identity, threshold range/calibration state, and `(None, 10)` output shape. Missing, uncalibrated, or incompatible concern artifacts produce an unavailable status and no fallback result.

## API And MongoDB

- `POST /api/skin-type/{upload_id}/analyze`
- `GET /api/skin-type/{upload_id}`
- `GET /api/models/skin-type/status`

`skin_type_reports` stores public report/upload/preprocessing IDs, JWT-derived owner, model/version, top and second classes/confidences, margin, full probabilities, questionnaire oiliness/dryness, sensitivity, agreement, final estimate/status, explanation, issues, and UTC timestamps. Unique `upload_id` prevents duplicates. No image bytes, derivative paths, tokens, identity features, or diagnoses are stored.

- `POST /api/skin-concerns/{upload_id}/analyze`
- `GET /api/skin-concerns/{upload_id}`
- `GET /api/models/skin-concerns/status`

`skin_concern_reports` stores the JWT-derived owner, upload and prerequisite report IDs, model/version, internal full-precision scores and calibrated thresholds, cautious interpreted results, questionnaire comparison, region availability, limitations, and UTC timestamps. Unique `upload_id` prevents duplicates. Public responses contain no internal path or image data and omit clearly not-observed labels.

- `POST /api/product-recommendations/{upload_id}/generate`
- `GET /api/product-recommendations/{upload_id}`
- `GET /api/product-recommendations/{upload_id}/products/{product_id}`

`product_recommendation_reports` stores owner and prerequisite IDs, catalogue and engine versions, validated scoring configuration, compact candidate score results, selected recommendations, confidence, limitations, and UTC timestamps. A unique upload index prevents duplicate reports. It stores no image data, paths, tokens, or full private profiles.

## Safety, Privacy, And Ethics

- No medical diagnosis, face recognition, protected-attribute prediction, dermatologist-equivalence claim, or guaranteed suitability.
- No training on unlicensed images or ordinary user uploads.
- No hidden low confidence or image/questionnaire disagreement.
- No image-based sensitivity class.
- Redness never confirms sensitivity, allergy, irritation, or a diagnosis.
- Mild/moderate/prominent describes visible prominence only, not clinical severity.
- Global model scores are not represented as precise localization; unavailable region geometry is disclosed.
- Private images and derivatives remain temporary and ownership-scoped.
- Probabilities are model outputs, not certainty.
- Severe, painful, infected, persistent, or unusual concerns require qualified professional advice.

## Known Limitations

- Dataset acquisition, training, evaluation, and legitimate artifact export are still incomplete.
- Performance and fairness are unknown until representative data is available.
- Skin-type labels themselves may be subjective and annotation criteria need documentation.
- Whole-image and questionnaire evidence cannot replace clinical assessment.
- Local storage/cleanup and in-process model locking are MVP infrastructure.
- A representative concern dataset, real training, threshold calibration, test evaluation, and fairness review are still pending.
- Global concern classification cannot provide validated precise regions.
- Step 11 filters catalogue products into eligible, caution, excluded, and insufficient-information groups using trusted profile and analysis data. It does not rank products or guarantee suitability.
- Step 12 ranking is a transparent relevance heuristic over fictional catalogue data. It does not establish clinical safety, product effectiveness, live stock, or an allergy guarantee.

## Product Eligibility Filtering

The protected eligibility stage combines self-reported allergies, avoided ingredients, fragrance preference, sensitivity, age group, INR budget, country, stored skin-type uncertainty, and stored visible-concern relevance with structured catalogue records. Hard conflicts are immutable, incomplete critical data is not silently accepted, and every decision contains stable reason codes. One owner-scoped report is stored per upload and may be updated by re-evaluation.

Allergy matching uses controlled aliases and exact ingredient/taxonomy relationships rather than unsafe substring checks. Country availability and price/source freshness are dated catalogue observations, not real-time inventory. Demo products remain visibly fictional. See `product-eligibility.md` for the complete rule and API contract.

Image-based skin-type estimation is a technical heuristic for general skincare guidance. It does not diagnose a skin condition or guarantee later AI accuracy.
