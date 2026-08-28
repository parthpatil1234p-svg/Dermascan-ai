# Dataset Location

Place only licensed, consented skin-type data in `raw/` and create `manifest.csv` with:

```text
image_id,relative_path,skin_type_label,source,license,subject_id,split,image_width,image_height,quality_status,notes
```

Allowed labels are `normal`, `oily`, `dry`, and `combination`. Application user uploads must not be used for training unless separate model-training consent has been obtained. Analysis consent is insufficient.

The raw, interim, and processed directories are ignored by Git. Dataset licensing, annotation criteria, subject identifiers, demographic coverage, and known fairness limitations must be documented before training.
