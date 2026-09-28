# Phase 1 Dataset Acquisition Report

## Scope

This report covers only Phase 1 (Dataset Acquisition) for `CV-Assurance-Dataset-v1`. No images were selected, no manifests were created, no attacks were generated, and no application code was modified.

## Download source

Official COCO dataset host:

- Validation images: `http://images.cocodataset.org/zips/val2017.zip`
- Train/validation annotations: `http://images.cocodataset.org/annotations/annotations_trainval2017.zip`

Download date: **2026-09-28** (Asia/Calcutta)

The official HTTP endpoints were used because the Windows HTTPS client rejected the host certificate with a target-principal mismatch. Archive readability, extraction, contents, and local SHA-256 hashes were verified after download.

## Files obtained

| File | Size (bytes) | Size (MiB) | SHA-256 |
|---|---:|---:|---|
| `datasets/raw/val2017.zip` | 815,585,330 | 777.80 | `4F7E2CCB2866EC5041993C9CF2A952BBED69647B115D0F74DA7CE8F4BEF82F05` |
| `datasets/raw/annotations_trainval2017.zip` | 252,907,541 | 241.19 | `113A836D90195EE1F884E704DA6304DFAAECFF1F023F49B6CA93C4AAAE470268` |

## Extraction result

- `val2017.zip` contained 5,000 JPEG entries beneath its standard `val2017/` directory. The directory component was stripped during extraction so that the image files are directly under `datasets/raw/images/`.
- `annotations_trainval2017.zip` contained six JSON files beneath its standard `annotations/` directory. It was extracted under `datasets/raw/`, placing the JSON files directly under `datasets/raw/annotations/`.
- Both extraction commands completed successfully.

Extracted image total: **814,705,164 bytes** across **5,000 files**.

Extracted annotation files:

| File | Size (bytes) | Size (MiB) |
|---|---:|---:|
| `captions_train2017.json` | 91,865,115 | 87.61 |
| `captions_val2017.json` | 3,872,473 | 3.69 |
| `instances_train2017.json` | 469,785,474 | 448.02 |
| `instances_val2017.json` | 19,987,840 | 19.06 |
| `person_keypoints_train2017.json` | 238,884,731 | 227.82 |
| `person_keypoints_val2017.json` | 10,020,657 | 9.56 |

Total extracted annotation size: **834,416,290 bytes** across **6 JSON files**.

## Verification result

Status: **PASS**

- Extracted image file count: **5,000**
- Extracted JPEG count: **5,000**
- Unexpected files in the image directory: **0**
- Unexpected subdirectories in the image directory: **0**
- Required annotation JSON exists: `datasets/raw/annotations/instances_val2017.json`
- `instances_val2017.json` parsed successfully.
- Image records in `instances_val2017.json`: **5,000**
- Object annotation records in `instances_val2017.json`: **36,781**
- Category records in `instances_val2017.json`: **80**
- Archive indexes were readable, and both archives extracted without errors.

Verified folder structure:

```text
datasets/
`-- raw/
    |-- images/
    |   `-- 5000 JPEG files
    |-- annotations/
    |   `-- 6 JSON files
    |-- val2017.zip
    `-- annotations_trainval2017.zip
```

## Issues requiring user action

None. Phase 1 is complete and ready for user approval before Phase 2 begins.
