# Step 15 Feedback

## Purpose And Boundaries

Step 15 collects optional, self-reported feedback about analysis results, broad skin-type estimates, visible observations, recommended products, product experience, routines, final reports, and the application. Feedback does not validate medical conclusions, confirm an allergy, establish product safety, become a public review, or automatically retrain a model. Historical report snapshots remain unchanged.

## Categories, Ratings, And Reasons

The eight controlled categories are `analysis_feedback`, `skin_type_feedback`, `skin_concern_feedback`, `product_recommendation_feedback`, `product_experience_feedback`, `routine_feedback`, `report_feedback`, and `application_feedback`. Ratings are optional category-specific integers from 1 (Very Poor) through 5 (Excellent). Stable positive, negative, and product-experience reason codes are returned by `GET /api/feedback/options`; analytics never has to infer every signal from comment text.

Skin-type feedback stores `matches_experience`, `partially_matches`, `does_not_match`, or `not_sure` without replacing the model result. Visible-observation feedback is restricted to observation codes in the owned final report. Product feedback is restricted to products in the owned report-time recommendation snapshot, so price and availability feedback cannot silently rewrite historical values.

## Product Experience And Avoidance

Product-experience feedback requires confirmation that the product was used. `no_issue`, `mild_discomfort`, `visible_irritation`, `serious_reaction`, and `not_sure` describe only the user's report. The UI displays non-diagnostic safety guidance. When the user explicitly selects future exclusion after meaningful discomfort, `user_product_avoidance` stores a private `USER_REPORTED_PRODUCT_AVOIDANCE` signal. The Step 11 eligibility engine treats an active entry as a hard exclusion for that user only. Users can remove the preference; it is never labelled a verified allergy or global product-safety finding.

## Consent, Withdrawal, And Moderation

`consent_for_analytics` and `consent_for_research_review` are independent, optional, and false by default. Image-processing consent does not carry over. Withdrawal changes status to `withdrawn`, clears both consents, removes the entry from active analytics, and deactivates its private improvement and avoidance signals. Minimal audit data is retained for the MVP.

Comments are limited by `FEEDBACK_MAX_COMMENT_LENGTH`, stripped of control characters, HTML-escaped, and never executed as markup. Potential script injection, contact information, excessive repetition, and unsupported medical claims are flagged separately. Admin moderation uses the existing `is_admin` authorization dependency and writes an audit entry.

## Aggregates And Review Signals

Only active or edited, unflagged feedback with analytics consent enters aggregates. `feedback_analytics_snapshots` contains counts, averages, percentages, and reason-code frequencies, but no user ID, email, name, raw comment, allergy list, image information, or filesystem path. Sparse grouped reasons are suppressed below `FEEDBACK_ANALYTICS_MIN_GROUP_SIZE`.

Price-changed, unavailable-product, and label-changed reason codes create `catalogue_review_signals` with counts and review status. They require manual or verified-source review and never update catalogue data automatically. Recommendation improvement signals are controlled future inputs, not model-training records.

## API And Collections

- `POST /api/feedback`
- `GET /api/feedback` with pagination and owner-scoped filters
- `GET|PUT|DELETE /api/feedback/{feedback_id}`
- `GET /api/feedback/options`
- `GET /api/feedback/product-avoidance`
- `DELETE /api/feedback/product-avoidance/{product_id}`
- `GET|PATCH /api/admin/feedback...`
- `GET|PATCH /api/admin/catalogue-review-signals...`

Collections are `user_feedback`, `user_product_avoidance`, `recommendation_improvement_signals`, `catalogue_review_signals`, `feedback_analytics_snapshots`, and `feedback_moderation_audit`. User ownership is always derived from the JWT. Public responses omit MongoDB IDs, tokens, image/path data, and internal payload hashes.

## Validation And Testing

The backend validates category-specific requirements, report/product ownership, rating ranges, reason codes, comment length, duplicate payloads, per-hour rate limits, and immutable edit relationships. Run `pytest` in `backend`; tests use synthetic report/product records and in-memory collections. Run `npm run build` in `frontend` and manually verify all protected routes, category fields, irritation guidance, consent defaults, editing, withdrawal, responsive layout, and readable API errors.

User feedback is self-reported information. It does not automatically validate medical conclusions, product safety, or AI model accuracy.
