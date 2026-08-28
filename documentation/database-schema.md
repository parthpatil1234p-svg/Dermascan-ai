# Database Schema

MongoDB ObjectIds are internal. Public IDs are random UUID-like strings. All
owner-scoped collections store a backend-derived `user_id` and UTC timestamps.

| Collection | Purpose | Primary indexes | Ownership and retention |
| --- | --- | --- | --- |
| `users` | Account and password hash | unique `email` | Own public fields; persistent |
| `skin_profiles` | Self-reported preferences | unique `user_id` | Own CRUD; persistent |
| `image_uploads` | Temporary upload metadata | unique `upload_id`; `user_id`; `expires_at` | Own read/delete; bytes expire |
| `image_quality_reports` | Technical image metrics | unique `quality_report_id`; unique `upload_id`; `user_id` | Own read; no bytes |
| `face_detection_reports` | Detection result and temporary crop reference | unique `face_report_id`; unique `upload_id`; `expires_at` | Own read; crop expires |
| `image_preprocessing_reports` | Transform contract and private derivative | unique `preprocessing_report_id`; unique `upload_id`; `expires_at` | Own read; derivative expires |
| `skin_type_reports` | Model probabilities and questionnaire comparison | unique public ID; unique `upload_id`; `user_id` | Own read; persistent metadata |
| `skin_concern_reports` | Multi-label visible observations | unique public ID; unique `upload_id`; `user_id` | Own read; persistent metadata |
| `brands` | Controlled brand metadata | unique `brand_id`; unique normalized name | Public active read; admin write |
| `ingredients` | Controlled ingredient taxonomy | unique `ingredient_id`; unique normalized name | Public read; seeded/admin data |
| `products` | Product catalogue | unique `product_id`; unique `slug`; text and filter indexes | Public active read; admin write |
| `product_import_jobs` | Import audit | unique job ID; created time | Admin only |
| `product_eligibility_reports` | Hard/soft filter decisions | unique public ID; unique `upload_id`; `user_id` | Own read; persistent metadata |
| `product_recommendation_reports` | Ranked eligible candidates | unique public ID; unique `upload_id`; `user_id` | Own read; persistent metadata |
| `skincare_routine_reports` | Deterministic AM/PM routine | unique public ID; unique `upload_id`; `user_id` | Own read; persistent metadata |
| `final_skin_reports` | Versioned report snapshots | unique `final_report_id`; unique upload/version; user/date | Own read/archive; no image bytes |
| `user_feedback` | Optional feedback and consent | unique `feedback_id`; user/date; references | Own CRUD/withdraw; admin moderation |
| `user_product_avoidance` | Private future exclusion | unique user/product | Own control; active preference |
| `recommendation_improvement_signals` | Consent-scoped private signal | unique source/type; `user_id` | Internal only |
| `catalogue_review_signals` | Manual-review aggregate | unique `signal_id`; product/type | Admin only; never auto-edits products |
| `feedback_analytics_snapshots` | De-identified grouped snapshot | unique snapshot ID; created time | Admin only; minimum group size |
| `feedback_moderation_audit` | Moderation history | `feedback_id` | Admin only |

Index creation runs idempotently during MongoDB connection startup. Recommendation
engines read only non-excluded eligibility records; user-reported avoidance is a
private hard exclusion and is not represented as a verified allergy.

