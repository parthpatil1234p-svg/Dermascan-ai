# AI And Image Components

## Component Classification

| Component | Implementation | Trained model |
| --- | --- | --- |
| File validation | Pillow decoding and configured rules | No |
| Image quality | OpenCV/NumPy technical heuristics | No |
| Face detection | MediaPipe library component | Library model, not project-trained |
| Preprocessing | OpenCV/NumPy transforms | No |
| Skin type | Exported Keras softmax classifier when artifacts exist | Yes |
| Visible concerns | Exported Keras multi-label classifier when artifacts exist | Yes |
| Eligibility/recommendations/routine | Deterministic rules and weighted scoring | No |

## Required Artifacts

Skin type requires `skin_type_model.keras`, metadata JSON, and the fixed class
map `normal`, `oily`, `dry`, `combination`. Visible concerns require the Keras
model, metadata, label map, and calibrated threshold JSON. Model loading checks
input width, height, channels, colour space, normalization, resize mode, output
shape, labels, and version metadata.

The repository intentionally does not contain trained model binaries or claimed
evaluation metrics. Health reports model availability honestly. Readiness is
`not_ready` when required artifacts are absent and demonstration mode is off.

## Training And Evaluation

The `ml` workspace contains dataset validation, split, training, threshold
calibration, evaluation, and export scripts. A valid evaluation must document
dataset source/license/version, subject-aware split limitations, class balance,
accuracy, precision, recall, F1, confusion matrix, per-class or multi-label
metrics, threshold selection, calibration, and fairness limitations.

No accuracy, clinical validity, user count, or coverage number is claimed until
it is produced by an executed evaluation against licensed held-out data.

## Demonstration Mode

`AI_DEMO_MODE=false` is the default. When explicitly set to `true`, registries
use deterministic image-statistic mock outputs. API responses, database reports,
final reports, and the frontend label them `demonstration`. Concern thresholds
are marked uncalibrated and final reports include a limitation. Demo outputs are
not valid model evaluation records and must not be used to report performance.

## Limitations

- Broad skin type and visible characteristics can be affected by illumination,
  camera processing, makeup, pose, skin tone, and dataset representation.
- Image analysis does not infer allergy, sensitivity, identity, ethnicity,
  protected attributes, or disease.
- Softmax and sigmoid outputs are not medical certainty.
- Face-region-specific validation remains limited by the detector and global
  concern model design.

DermaScan AI provides general skincare guidance only. It is not clinically
validated and does not prescribe treatment.

