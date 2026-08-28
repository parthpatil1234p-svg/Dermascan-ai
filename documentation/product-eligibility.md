# Product Eligibility Filtering

## Purpose And Boundary

Step 11 removes products with known conflicts, identifies caution factors, and preserves records that cannot be evaluated because critical catalogue data is incomplete. It uses the authenticated user's stored skin profile, completed skin-type report, completed visible-concern report, and active public catalogue. The client cannot submit or replace those trusted inputs.

Eligibility filtering does not rank products, prescribe treatment, diagnose a condition, or guarantee that a product will be safe or effective. Step 12 may rank only the non-excluded candidate set and must never reintroduce a hard exclusion.

## Statuses

| Status | Meaning |
| --- | --- |
| `eligible` | Enough data is available and no hard conflict or caution was found. |
| `eligible_with_caution` | No hard conflict was found, but one or more review conditions apply. |
| `excluded` | At least one immutable hard exclusion applies. |
| `insufficient_information` | Critical product data is missing, unknown, invalid, or contradictory. |

Status priority is `excluded`, then `insufficient_information`, then `eligible_with_caution`, then `eligible`. Positive compatibility evidence never changes a hard exclusion.

## Normalized Filtering Context

The backend builds the context from MongoDB. It normalizes country names to ISO codes, fragrance options to controlled values, product/brand text to normalized keys, allergies to controlled concepts, and avoided ingredients to exact ingredient or taxonomy-category identifiers. It preserves the original allergy and avoidance text in the internal report for explainability. Uncertain skin-type output remains `uncertain` and is not used as a hard class.

The current profile contract treats a supplied minimum and maximum INR budget as mandatory. No budget values means no budget constraint. The engine supports a flexible context with `BUDGET_SOFT_OVERAGE_PERCENT`, ready for a future explicit profile option.

## Allergy And Ingredient Policy

Aliases such as fragrance, perfume, parfum, and added fragrance map to `added_fragrance`. Other controlled concepts include essential oils, drying alcohol, retinoids, and benzoyl peroxide. Matching uses canonical taxonomy records, normalized aliases, explicit allergen flags, and explicit ingredient categories. Substring matching is not used.

- A verified known-allergy match uses `KNOWN_ALLERGY_MATCH` and excludes the product.
- An exact or category-level avoided ingredient uses `USER_AVOIDED_INGREDIENT_MATCH` and excludes the product.
- An unmapped allergy produces a strong `POTENTIAL_ALLERGEN_PRESENT` caution. When ingredient data is incomplete, the product becomes `insufficient_information`.
- Missing ingredient data during allergy or avoidance checks uses `INGREDIENT_LIST_MISSING`.
- Unmapped catalogue ingredients use `UNMAPPED_CRITICAL_INGREDIENT` and are not silently accepted.

Messages describe a data match, never a guaranteed reaction.

## Fragrance And Sensitivity

`Fragrance-free only` excludes records known to contain added fragrance or fragrant ingredients. Unknown fragrance status becomes insufficient information. `Prefer fragrance-free` adds a caution without exclusion. `No preference` adds no fragrance preference rule, although known-allergy rules still apply.

For self-reported sensitivity, `potentially_suitable` is positive evidence. `use_with_caution`, unknown suitability, exfoliating acids, retinoids, benzoyl peroxide, drying alcohol, added fragrance, essential oils, and multiple high-activity flags add cautions. These are review prompts, not treatment instructions or automatic medical contraindications.

## Budget, Price, And Availability

- Strict budget: prices outside the explicit minimum/maximum are excluded; equality is accepted.
- Flexible budget: an overage within `BUDGET_SOFT_OVERAGE_PERCENT` is a caution; a larger overage is excluded.
- Missing or unsupported-currency price with a strict budget is insufficient information.
- `PRODUCT_PRICE_STALE_DAYS` adds `PRICE_DATA_STALE` without guessing a new price.
- Available in the normalized country is positive evidence.
- Limited availability is a caution, unavailable is excluded, and unknown is insufficient information.
- `PRODUCT_AVAILABILITY_STALE_DAYS` adds a freshness caution. No real-time inventory claim is made.

## Compatibility And Data Quality

An exact broad skin-type or `all_skin_types` mapping is positive evidence. A mismatch is a caution, not a hard medical exclusion. Uncertain skin type avoids class-based exclusion. Visible concern overlap is positive relevance only; it is never described as treatment evidence. Basic cleanser, moisturizer, and sunscreen products are not excluded solely for lacking a concern mapping.

The quality gate checks active/public status, supported category, demo-flag consistency, price and availability structure, source freshness, ingredient completeness, and taxonomy mapping. Fictional demo records may continue only with a visible `DEMO_PRODUCT` caution and label. Draft/inactive records are excluded by the rule engine and are omitted from the normal active-public API catalogue query.

Age is taken only from the profile. Verified product age bounds are enforced. The conservative MVP excludes under-18 retinoid-flagged products and unsupported categories; it does not infer age from an image or invent clinical restrictions.

## Deterministic Rule Order

1. Product data quality and public status.
2. Known allergy conflicts.
3. User avoided ingredients and categories.
4. Verified age restrictions.
5. Country availability and freshness.
6. Budget and price freshness.
7. Self-reported sensitivity cautions.
8. Fragrance preference.
9. Skin-type compatibility.
10. Visible-concern relevance.

All applicable reasons are collected where practical. Hard exclusions remain final.

## Stable Reason Codes

Allergy and ingredients: `KNOWN_ALLERGY_MATCH`, `USER_AVOIDED_INGREDIENT_MATCH`, `POTENTIAL_ALLERGEN_PRESENT`, `INGREDIENT_LIST_MISSING`, `INGREDIENT_DATA_INCOMPLETE`, `UNMAPPED_CRITICAL_INGREDIENT`, `FRAGRANCE_CONFLICT`, `ESSENTIAL_OIL_CONFLICT`, `DRYING_ALCOHOL_CAUTION`, `EXFOLIATING_ACTIVE_CAUTION`, `RETINOID_CAUTION`, `BENZOYL_PEROXIDE_CAUTION`.

Budget and availability: `PRICE_WITHIN_BUDGET`, `PRICE_NEAR_BUDGET_LIMIT`, `PRICE_ABOVE_BUDGET`, `PRICE_UNKNOWN`, `PRICE_DATA_STALE`, `AVAILABLE_IN_USER_COUNTRY`, `LIMITED_AVAILABILITY`, `UNAVAILABLE_IN_USER_COUNTRY`, `AVAILABILITY_UNKNOWN`, `AVAILABILITY_DATA_STALE`.

Compatibility and general: `SKIN_TYPE_MATCH`, `SKIN_TYPE_PARTIAL_MATCH`, `SKIN_TYPE_MISMATCH`, `VISIBLE_CONCERN_MATCH`, `NO_VISIBLE_CONCERN_MATCH`, `SENSITIVITY_POTENTIALLY_SUITABLE`, `SENSITIVITY_USE_WITH_CAUTION`, `SENSITIVITY_NOT_SPECIFIED`, `PRODUCT_INACTIVE`, `PRODUCT_UNVERIFIED`, `PRODUCT_DATA_CONTRADICTION`, `AGE_GROUP_RESTRICTION`, `CATEGORY_NOT_ALLOWED`, `DEMO_PRODUCT`, `SOURCE_DATA_STALE`.

## API

- `POST /api/product-eligibility/{upload_id}/evaluate` verifies JWT ownership and prerequisites, evaluates the active public catalogue, upserts the report, and returns a safe paginated summary.
- `GET /api/product-eligibility/{upload_id}` returns the existing owned report without rerunning. Query options are `status`, `category`, `page`, and `page_size`.
- `GET /api/product-eligibility/{upload_id}/products/{product_id}` returns a safe product summary plus hard exclusions, cautions, positive matches, information gaps, demo status, freshness fields, and disclaimer.

Missing and cross-user uploads/reports use `404` without revealing ownership. Missing prerequisites and empty catalogues use `409`. Unexpected failures use a generic `500` and do not become a user-specific safety conclusion.

## MongoDB And Workflow

`product_eligibility_reports` stores the public report ID, authenticated user ID, upload ID, prerequisite profile/report IDs, catalogue and engine versions, normalized internal filtering context, compact product decisions and reasons, summary counts/codes, and UTC timestamps. It stores no image bytes, paths, credentials, tokens, diagnoses, or recommendation scores.

Unique indexes on `eligibility_report_id` and `upload_id` prevent duplicates; `user_id` is indexed for ownership queries. Re-evaluation preserves `created_at` and the public report ID while updating results and `updated_at`.

The upload moves from a completed concern state to `product_eligibility_evaluating`, then `recommendation_scoring_pending` on success. A server failure uses `product_eligibility_failed`; it is not stored as a product safety decision.

## Privacy And Frontend

`/product-eligibility` is protected by all earlier workflow guards. It starts evaluation once, shows progress, status counts, category/status filters, pagination, transparent product reasons, demo labels, and safe on-demand details. Only upload/product IDs and non-sensitive report filters are sent. Allergies, profile data, raw images, and tokens are never placed in public URLs or eligibility state storage.

## Verification

```powershell
cd backend
pytest

cd ..\frontend
npm run build
```

The isolated backend suites cover aliases, safe exact matching, all four statuses, strict/flexible budgets, availability, freshness, compatibility uncertainty, age rules, rule priority, ownership, report upsert, pagination, details, and workflow state.

## Limitations

- The bundled product records are fictional demonstrations, not retail advice.
- Catalogue completeness and source freshness determine filtering quality.
- Unmapped free-text allergy terms require manual label review.
- Availability is a dated catalogue observation, not live inventory.
- Eligibility cannot guarantee no irritation, allergy, effectiveness, or medical suitability.
- Recommendation scoring, ranking, product selection, and routines are not implemented in Step 11.
