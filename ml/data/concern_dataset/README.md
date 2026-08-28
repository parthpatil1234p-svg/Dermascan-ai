# Visible Concern Dataset

No dataset is bundled. Add only images with documented usage permission and a manifest at `manifests/manifest.csv`. Raw and processed data are ignored by Git.

Required columns:

```text
image_id,relative_path,subject_id,source,license,split,visible_oiliness,dry_looking_areas,visible_pores,visible_redness,uneven_looking_tone,dark_spots,acne_like_spots,under_eye_darkness,dull_looking_appearance,fine_line_visibility,annotation_quality,annotator_count,notes
```

Concern values are `0`, `1`, or empty/`null` for unknown. Unknown annotations are masked and must never be converted to negatives. Ordinary application-analysis consent is not model-training consent.

## Annotation Guide

- `visible_oiliness`: visible shine or reflective appearance, especially around the T-zone.
- `dry_looking_areas`: visible rough, flaky, matte, or patchy-looking areas.
- `visible_pores`: clearly noticeable pore-like texture.
- `visible_redness`: areas appearing redder than surrounding skin, without diagnosing sensitivity or disease.
- `uneven_looking_tone`: visible variation in facial colour or brightness.
- `dark_spots`: localized darker-looking spots relative to surrounding skin.
- `acne_like_spots`: visible raised or coloured spot-like areas; never clinical acne diagnosis.
- `under_eye_darkness`: areas below the eyes appearing darker than nearby cheek regions.
- `dull_looking_appearance`: low visible radiance or uneven overall brightness.
- `fine_line_visibility`: small visible line-like textures, without inferring age or disease.

Annotation quality is `high`, `medium`, `low`, or `unknown`. Record annotator count and review disagreement. Dataset documentation must summarize source licenses, label distribution, skin-tone/age/lighting/camera coverage where ethically available, and known annotation/fairness limitations.
