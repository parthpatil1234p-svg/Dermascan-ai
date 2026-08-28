# Local Model Artifacts

Run the ML validation, training, evaluation, and export commands documented in `ml/README.md`. Skin-type exports place `skin_type_model.keras`, `skin_type_model_metadata.json`, `class_map.json`, and `model_metrics.json` here. Visible-concern exports place `skin_concern_model.keras`, `skin_concern_model_metadata.json`, `skin_concern_label_map.json`, `skin_concern_thresholds.json`, and `skin_concern_metrics.json` here.

Model binaries and generated evaluation artifacts are ignored by Git. Each backend model endpoint reports unavailable until all of its required compatible artifacts are installed. No placeholder predictions are generated.
