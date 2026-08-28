# Personalized Product Recommendations

## Purpose And Boundary

Step 12 ranks the Step 11 catalogue candidates that are already `eligible` or `eligible_with_caution`. Products marked `excluded` or `insufficient_information` never enter the scoring engine. Ranking estimates project-specific relevance from stored profile and analysis evidence; it is not a medical suitability score, prescription, guarantee, or diagnosis.

The engine trusts only owner-scoped MongoDB reports and catalogue records. The request contains only the public upload ID. User IDs, profile answers, image data, eligibility decisions, and scores are not accepted from the client.

## Score Formula

Each component is normalized to `0-100`. Full-precision values are used until the public response is produced.

```text
base_score =
    skin_type_match * 0.25
  + visible_concern_match * 0.25
  + ingredient_relevance * 0.15
  + sensitivity_compatibility * 0.10
  + budget_fit * 0.10
  + availability * 0.05
  + brand_preference * 0.04
  + data_quality * 0.03
  + rating * 0.03

final_score = clamp(base_score - capped_penalties, 0, 100)
```

Weights are environment settings and must total `1.0`. Startup validation rejects an invalid total. Penalties are applied once by stable code, grouped to prevent duplicate deductions, and capped at `30` by default. Cautions reduce ranking; they never erase an exclusion or manufacture missing safety evidence.

## Component Behavior

- Skin type compares the saved broad estimate with structured product suitability. An uncertain estimate receives conservative broad-match credit and never a confident exact-match claim.
- Visible concerns use only saved observed/possible labels and category-aware concern relevance. A basic category can receive a neutral baseline without inventing a concern.
- Ingredient relevance uses controlled ingredient roles and taxonomy, not substring matching or unsupported treatment claims.
- Sensitivity compatibility combines self-reported sensitivity, catalogue sensitivity suitability, fragrance information, and known caution flags.
- Budget fit is gradual. Strict over-budget products should already be excluded; flexible overage loses points progressively.
- Availability reflects the stored country snapshot and is not real-time inventory.
- Brand preference is a small preference signal and cannot override safety rules.
- Data quality rewards verified, complete, fresh catalogue records. Demo products remain visibly labelled.
- Rating uses a Bayesian prior so products with very few reviews cannot dominate. Missing ratings receive neutral, not perfect, credit.

## Penalties, Bands, And Confidence

Default penalties cover eligibility caution, unspecified sensitivity, active-ingredient caution, fragrance conflict, stale price or availability, limited availability, significant information gaps, and uncertain skin type. The default score bands are `Excellent Match`, `Strong Match`, `Good Match`, `Moderate Match`, and `Low Match`; products below `RECOMMENDATION_MIN_DISPLAY_SCORE=60` are not selected.

Recommendation confidence is separate from the match score. It reflects profile completeness, model/report certainty, catalogue quality and freshness, caution burden, and score separation. Confidence is capped at moderate when the saved skin-type result is uncertain. It does not mean medical certainty.

## Category Selection And Diversity

Results are grouped into cleanser, serum, moisturizer, and sunscreen. Selection is deterministic and defaults to two products per category. It applies a same-brand cap, removes near-identical ingredient profiles, and prefers an alternate price tier when scores are close. Stable ties use score, caution count, data quality, freshness, concern score, budget score, product name, and product ID in that order.

The engine may return no recommendations. It never lowers the display threshold or reintroduces excluded/insufficient candidates merely to fill a category.

## Explainability

Every selected product includes a concise explanation, evidence-backed positive factors, caution factors, component scores, applied penalties, score band, and independent confidence. Messages are generated from actual stored evidence and use cautious language such as `aligned with` and `may be relevant`.

## API And Storage

- `POST /api/product-recommendations/{upload_id}/generate` generates or updates the owner-scoped report.
- `GET /api/product-recommendations/{upload_id}` retrieves the report with category, minimum-score, and pagination filters.
- `GET /api/product-recommendations/{upload_id}/products/{product_id}` returns a safe recommendation detail.

`product_recommendation_reports` has unique indexes on `recommendation_report_id` and `upload_id`, plus an owner index. It stores prerequisite report IDs, catalogue/scoring versions, the exact configuration snapshot, compact candidate score results, selected recommendations, confidence and limitations, and UTC timestamps. It stores no image bytes, paths, tokens, passwords, or complete product documents.

## Workflow And Statuses

The normal transition is `recommendation_scoring_pending` to `recommendation_scoring`, then `recommendations_completed` or `recommendations_completed_with_limitations`, followed by deterministic routine generation and final-report aggregation. A temporary server failure uses `recommendations_failed` and can be retried without changing eligibility decisions.

## Configuration

All `RECOMMENDATION_WEIGHT_*`, `PENALTY_*`, `RECOMMENDATION_MIN_DISPLAY_SCORE`, `RECOMMENDATION_MAX_PER_CATEGORY`, and `RECOMMENDATION_MAX_SAME_BRAND` values are listed in `backend/.env.example`. These are initial college-project heuristics and should be tuned only with documented validation, versioning, and regression tests.

## Testing And Limitations

Backend tests cover component boundaries, weighting, penalty caps, bands, candidate isolation, deterministic ranking, diversity, explanations, confidence, authorization, ownership, prerequisites, report upsert, safe responses, and empty results. Run `pytest` from `backend`; run `npm run build` from `frontend`.

The bundled catalogue is fictional and availability is not live. Model-dependent workflow stages still require legitimate exported artifacts. The engine does not inspect image bytes, infer allergies, guarantee effectiveness, or replace patch testing. Later routine and final-report stages preserve these recommendation boundaries.
