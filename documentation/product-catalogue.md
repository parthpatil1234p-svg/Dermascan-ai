# Step 10 Product Catalogue

## Purpose And Policy

The catalogue stores structured skincare product, brand, and ingredient information for search and later recommendation work. It currently performs catalogue filtering only; it does not calculate personalized recommendation rankings. Catalogue mappings identify broad general skincare goals and never mean that a product treats disease, is allergy-safe, or is suitable for every person.

Permitted data sources are official manufacturers, authorized retailers, licensed datasets, manually verified records, and clearly labelled synthetic records. Scraping, fabricated claims, invented real-product formulas, and invented ratings are prohibited. The included seed contains only fictional products and brands. Every product uses `data_type=demo_synthetic`, `is_demo_product=true`, and the public label `Demonstration Product - Not a Real Retail Listing`.

## Collections

`products` stores public product ID and slug, name/brand/category, concise description, source type, skin-type and visible-goal mappings, ordered source ingredients, canonical ingredient keys, caution flags, fragrance/sensitivity metadata, dated INR price, dated country availability, source verification, activity state, and UTC timestamps. Internal `_id`, import paths, and source import URLs are not returned publicly.

`ingredients` stores a public ingredient ID, canonical and normalized names, exact aliases, one controlled category, cautious cosmetic roles/notes, active state, and timestamps. Alias matching is exact after case-folding and whitespace normalization; no partial or approximate ingredient merging is performed. Ordered display ingredients remain separate from de-duplicated normalized keys, and unmapped values can be retained for manual review.

`brands` stores public ID, display and normalized name, optional supported origin/website facts, verification/activity flags, and timestamps. `product_import_jobs` stores only an import summary, counts, bounded row errors, status, and timestamps; it does not retain raw import files.

## Controlled Values

Categories are `cleanser`, `toner`, `serum`, `moisturizer`, `sunscreen`, `exfoliant`, `spot_care`, `under_eye_product`, `face_mask`, `night_cream`, and `lip_care`.

Skin mappings are `normal`, `oily`, `dry`, `combination`, `sensitive_self_reported`, and `all_skin_types`. The ten visible concern codes exactly match Step 9. These mappings express potential relevance to a general appearance goal, not treatment efficacy.

Ingredient categories are active, humectant, emollient, occlusive, surfactant, antioxidant, preservative, fragrance, essential oil, exfoliant, UV filter, soothing agent, colourant, solvent, and other. General caution flags do not make universal safety determinations.

## Price, Availability, And Sources

Prices are manual catalogue snapshots in INR and require `price_checked_at`. Availability requires ISO two-letter countries, status, and `availability_checked_at`. The UI warns when price is older than `PRODUCT_PRICE_STALE_DAYS` (30), availability is older than `PRODUCT_AVAILABILITY_STALE_DAYS` (14), or source review is older than `PRODUCT_SOURCE_VERIFICATION_STALE_DAYS` (90). These settings are tunable and do not provide real-time commerce data.

URLs accept only HTTP or HTTPS. Real records should prefer official sources, use concise original summaries, and record a verification date. Ratings are optional and require value, count, source, and checked date as one unit.

## API

- `GET /api/products`: paginated active public products; filters include search, brand, category, skin type, visible concern, included/excluded ingredient, country, availability, price range, fragrance, public data type, and whitelisted sort.
- `GET /api/products/{product_id}`: safe detail by public ID or slug.
- `GET /api/brands`: active brand search and pagination.
- `GET /api/ingredients`: active ingredient search, category filter, and pagination.
- `GET /api/ingredients/{ingredient_id}`: factual ingredient record and up to 20 matching public products.
- `/api/admin/products...`: JWT and server-side `is_admin` authorization for create, replace, patch, soft delete, import jobs, and statistics. Registration always creates `is_admin=false`.

Search input is escaped and bounded to 100 characters. Page size is capped at 100. Filters, country codes, price ranges, data types, and sort values are validated. Public queries always exclude inactive products and `unverified_draft` records. Soft delete sets `is_active=false`.

## Indexes

Products use unique indexes on `product_id` and `slug`, indexes on brand/category/skin types/concerns/ingredients/country/availability/activity/data type/price, and a text index over product name, brand, short description, and highlights. Ingredients use unique public ID and normalized-name indexes plus alias/category indexes. Brands use unique public ID and normalized-name indexes. Import jobs use unique job ID and created-date indexes.

## Seed And Import

```powershell
cd backend
python -m app.scripts.seed_ingredients
python -m app.scripts.seed_brands
python -m app.scripts.import_products --file data/products/demo_products.json --dry-run
python -m app.scripts.import_products --file data/products/demo_products.json
```

JSON imports contain a list of product objects. CSV imports use `|` for simple list fields and JSON text for nested ingredient, price, package, and rating fields. Validation reports bad rows explicitly. Dry-run writes an import summary but no product. Duplicate detection uses normalized name, exact brand, category, and package size; different package sizes remain separate.

## Frontend And Privacy

`/products`, `/products/:productId`, `/ingredients`, and `/ingredients/:ingredientId` are public factual catalogue views. `/product-discovery` remains protected by the completed profile, skin-type, and concern workflow. Filter state is shareable in the URL, but private profile fields, allergies, analysis reports, and personal identifiers are never added to catalogue URLs.

## Testing And Limitations

Run `pytest` in `backend` and `npm run build` in `frontend`. Tests cover schemas, invalid values, normalization, safe search, every primary filter, sorting, pagination, public visibility, details, import preview/import/update, admin authorization, soft deletion, and safe responses.

The dataset is synthetic and small, pricing and availability are dated manual snapshots, country support is currently India-focused, exact ingredient concentration is unknown, and no personalized scoring is implemented. Product data must be reviewed before any real listing is added.

