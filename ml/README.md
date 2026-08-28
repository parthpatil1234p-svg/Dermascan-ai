# Skin Type ML Workspace

This workspace supports four visual classes in fixed order: `normal`, `oily`, `dry`, `combination`. Sensitivity is intentionally excluded because it is self-reported and is not an image-only diagnosis.

No dataset, trained model, or performance metric is committed. Obtain a licensed, consented dataset, document annotation criteria and demographic coverage, populate `data/manifest.csv`, then run:

```bash
pip install -r requirements.txt
python scripts/validate_dataset.py
python scripts/split_dataset.py
python scripts/train_skin_type_model.py
python scripts/evaluate_skin_type_model.py --dataset-version YOUR_VERSION
python scripts/export_skin_type_model.py --dataset-version YOUR_VERSION
pytest
```

Training uses MobileNetV2 transfer learning: a frozen feature-extraction stage followed by limited upper-layer fine-tuning at a lower learning rate. Validation loss controls early stopping, checkpointing, and learning-rate reduction. The untouched test set is evaluated only after model selection.

Evaluation produces accuracy, macro precision/recall/F1, weighted F1, per-class metrics, cross-entropy loss, confusion matrix, confidence histogram, reliability diagram, expected calibration error, classification report, training-history plot, and a versioned evaluation report. No metric is populated without actual test-set evaluation.

Subject-level splitting is required when subject identifiers exist. If identity metadata is unavailable, leakage risk and fairness limitations must be documented. Dataset diversity analysis must assess skin tones, ages, lighting, cameras, gender representation, facial appearance, and geography without predicting protected attributes.

Training-only augmentation is conservative. Validation and test images are deterministic. User uploads are excluded unless separate model-training consent is collected.

## Visible Skin-Concern Workspace

Step 9 adds a separate multi-label pipeline for exactly ten controlled visual labels:

`visible_oiliness`, `dry_looking_areas`, `visible_pores`, `visible_redness`, `uneven_looking_tone`, `dark_spots`, `acne_like_spots`, `under_eye_darkness`, `dull_looking_appearance`, and `fine_line_visibility`.

These labels describe appearance only. They do not encode diseases, causes, sensitivity, allergies, protected attributes, or treatment needs. The annotation contract is in `data/concern_dataset/README.md`; the fixed output map and training configuration are in `configs/skin_concern_label_map.json` and `configs/skin_concern_training.yaml`.

```bash
python scripts/validate_concern_dataset.py
python scripts/split_concern_dataset.py
python scripts/train_skin_concern_model.py
python scripts/calibrate_concern_thresholds.py
python scripts/evaluate_skin_concern_model.py
python scripts/generate_concern_model_metadata.py
python scripts/export_skin_concern_model.py
pytest
```

Validation decodes real files; validates source, license, subject, and annotation fields; detects duplicate hashes and cross-split duplicates; and rejects subject leakage. Deterministic subject-aware splitting targets 70/15/15 while balancing positive labels where practical. Unknown annotations use a mask and are not treated as negative examples. Training computes positive class weights from the training split only.

The model uses MobileNetV2 with ten sigmoid outputs, weighted masked binary cross-entropy, frozen feature extraction, limited fine-tuning with batch normalization frozen, conservative training-only augmentation, validation-loss early stopping, best checkpointing, and learning-rate reduction. The input contract remains RGB `224 x 224 x 3`, letterbox, `float32`, normalized to 0-1 exactly once.

Threshold calibration maximizes per-label F1 on the validation split only. Test evaluation reports per-label precision, recall, F1, specificity, support, confusion counts, ROC-AUC and PR-AUC where defined, plus macro/micro/weighted F1, hamming loss, label-ranking average precision, and subset accuracy. It writes per-label confidence histograms, confusion matrices, precision-recall curves, and ROC curves where both classes are available. Export refuses to run without real model, metadata, validation-calibrated thresholds, and metrics artifacts.

No concern dataset, trained artifact, calibrated threshold, performance value, or fairness claim is included in this repository. Runtime model status must remain unavailable until legitimate artifacts are produced. Representative evaluation should document skin-tone, age, lighting, camera, makeup/filter, geography, and other relevant coverage without using the model to infer protected attributes.
