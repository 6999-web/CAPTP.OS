# CAPTP.OS Offline Training Pipeline

This folder defines the offline training workflow for shooting recognition enhancement.

## Structure

- `dataset/` dataset versioning and labeling conventions
- `configs/` model and training configuration templates
- `reports/` evaluation report outputs
- `exports/` exported weights and deployment mapping
- `scripts/` helper scripts for dataset validation and training orchestration

## Model Tracks

1. Pose fusion (online): MediaPipe + YOLO-Pose normalized inputs
2. Weapon fine-grained detection: `pistol`, `magazine`, `ejection_port`, `safety_switch`
3. Temporal sequence classification: BodyMTS-style multivariate time-series for correct vs incorrect workflow

## Deployment Profiles

- `lite` for low-power hardware (Orange Pi class): lower complexity and frame skip
- `standard` default runtime profile
- `high_precision` optional profile for stronger hardware
