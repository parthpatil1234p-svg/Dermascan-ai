# DermaScan AI Frontend

React and Vite frontend for the complete DermaScan AI college workflow. Step 16
adds route-level code splitting, global error/loading states, explicit demo-mode
notices, safer session restoration, automated unit/E2E checks, and a production
Nginx container while preserving the existing clinical-style design.

## Setup

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

`.env` must contain:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

The site normally runs at `http://localhost:5173`. Build with `npm run build`; if PowerShell blocks `npm.ps1`, use `npm.cmd run dev` or `npm.cmd run build`.

## Protected Workflow

1. Authenticate and complete the self-reported profile.
2. Upload, consent, validate image quality, detect one usable face, and preprocess the private crop.
3. `/skin-type-analysis` checks `/models/skin-type/status` before inference.
4. A compatible model triggers one `POST /skin-type/{upload_id}/analyze` request.
5. The result displays the broad estimate or `Uncertain`, confidence, all four probabilities, questionnaire agreement, sensitivity, explanation, and limitations.
6. `/skin-concern-analysis` verifies the concern-model artifact set, sends one real analysis request, and separates observed/possible labels from uncertain labels.
7. The report shows cautious explanations, image-prominence labels, relevant oiliness/dryness questionnaire comparison, region limitations, and safety guidance.
8. `/product-eligibility` verifies the completed concern flow and starts one backend eligibility evaluation for the active upload.
9. The page displays eligible, caution, excluded, and insufficient-information products with stable reasons and safe details.
10. `/product-recommendations` ranks only eligible and caution candidates, displays category groups and explanations, and never restores excluded products.
11. `/product-discovery` remains a separate full-catalogue view without private profile filtering or personalized ranking.
12. `/skincare-routine` creates ordered morning/night steps only from selected recommendations.
13. `/final-report` creates one trusted versioned snapshot and redirects to `/reports/:finalReportId`.
14. `/reports` lists owner-scoped history; `/reports/:finalReportId/print` provides the protected print view.
15. `/feedback` submits optional structured feedback; `/feedback/history` and `/feedback/:feedbackId` support review, editing, withdrawal, and private avoidance management.

Public routes `/products`, `/products/:productId`, `/ingredients`, and `/ingredients/:ingredientId` provide shareable, URL-synchronized search and factual details. Product filters never place allergies, profiles, or analysis results in URLs.

Missing model artifacts produce a clear unavailable screen and no fake values. Errors are reduced to readable messages; duplicate requests are blocked while analysis is active.

## State And Services

- `SkinTypeContext` owns safe report data, model status, request state, progress, errors, and continuation permission.
- `skinTypeService.js` uses the existing authenticated Axios client for analyze, get-report, and model-status requests.
- `SkinTypeRequiredRoute` prevents direct access to the next placeholder without a completed estimate or explicit uncertain result.
- `UploadRequiredRoute` recognizes pending, analyzing, estimated, uncertain, failed, and next-stage workflow states.
- `SkinConcernContext` owns concern model readiness, safe report data, one-request progress, errors, and continuation permission.
- `skinConcernService.js` reuses the authenticated Axios client for analyze, get-report, and readiness calls.
- `ConcernRequiredRoute` blocks direct access to product discovery without a completed concern report.
- `ProductEligibilityContext` owns the safe report, one-request progress, filters, product detail, and readable errors.
- `productEligibilityService.js` reuses the authenticated Axios client and sends only upload/product IDs plus non-sensitive report filters.
- `ProductRecommendationContext` owns one-request generation progress, the safe report/detail, category view, and readable errors.
- `productRecommendationService.js` reuses the authenticated Axios client for generation, report retrieval, and safe product detail.
- `EligibilityRequiredRoute` requires the stored Step 11 report before the recommendation page can render.
- `SkincareRoutineContext` owns the generated routine and its deterministic progress state.
- `FinalReportContext` owns final generation, detail/history loading, archive actions, and transient PDF downloads.
- `feedbackService.js` reuses the authenticated Axios client for controlled options, submit, history, edit, withdrawal, and avoidance requests. Raw comments are not stored in browser storage or URLs.

The frontend keeps safe workflow reports in React memory and stores only the
public active upload ID in `sessionStorage` so a refresh can verify and restore
the current workflow. It never stores a raw image, crop, processed image,
tensor, model file, physical path, password, or profile answers in browser
storage or query parameters.

## Result States

- Estimated: shows the selected broad class, confidence level/percentage, sorted probabilities, questionnaire agreement, sensitivity, explanation, limitations, replace-image action, and continue action.
- Uncertain: states that no class was forced and offers a clearer upload, profile review, or continuation with general guidance and no strong skin-type assumption.
- Model unavailable: instructs the project developer to install exported artifacts and offers a readiness retry without generating demo results.
- Request failure: shows a safe message and retry/replacement actions.

Probability bars are model output, not medical certainty. Sensitivity is explicitly labeled as self-reported and remains separate from the image classes.

Concern results may contain several independent labels. Confidence is model confidence, and mild/moderate/prominent describes visible prominence in one image rather than clinical severity. Borderline labels appear in a separate uncertain section. Without validated region geometry, the global model reports full-face scope and the interface displays that limitation rather than inventing localization.

## Verification

```powershell
npm run test
npm run lint
npm run build
npm run test:e2e
```

Manual verification should cover route protection, prerequisite redirects, one generation request, category tabs, score breakdowns, caution display, detail dialog, empty results, disabled loading controls, keyboard focus, mobile layout, readable errors, and browser-console health. Allergies, profile data, images, and tokens must not appear in report URLs.

## Limitations

- A legitimate exported backend model is required for live results.
- Safe report state remains in memory; after refresh, the active upload ID is
  verified and individual stages reload their owned backend report as needed.
- Full-source unit coverage is still low; Playwright currently covers the
  public shell, protected redirect, login validation, and responsive overflow.
- A legitimate exported concern model and calibrated per-label thresholds are required for live results.
- Precise concern localization is unavailable for the current global classifier.
- The catalogue contains synthetic demonstrations; eligibility does not guarantee safety, effectiveness, availability, or suitability.
- Final reports and PDFs exclude raw facial images. Reports remain project-specific general guidance and do not guarantee medical suitability, effectiveness, live availability, or allergy safety.
- Feedback consent boxes are optional and unselected by default. Feedback is not a public review, verified medical/product evidence, or automatic AI-training data.
- The frontend cannot make an uncalibrated model medically reliable.

DermaScan AI estimates broad visible skin behavior using a facial image and questionnaire responses. It does not diagnose skin diseases or replace a qualified dermatologist.
