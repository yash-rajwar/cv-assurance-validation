# CV-Assurance-Dataset-v1 Release Notes

## Release information

- Version: **CV-Assurance-Dataset-v1**
- Creation date: **2026-09-28** (Asia/Calcutta)
- Source: official COCO 2017 Object Detection validation images and train/validation annotation package
- Release form: directory package

## Dataset statistics

| Statistic | Value |
|---|---:|
| Raw COCO validation images | 5,000 |
| Selected clean images | 1,000 |
| Development images | 800 |
| Frozen holdout images | 200 |
| COCO categories represented | 80 / 80 |
| Clean manifest records | 1,000 |
| Records with object instances | 989 |
| Valid COCO negative samples | 11 |
| Object annotations represented | 8,890 |
| Bounding boxes represented | 8,890 |

The 11 valid COCO negative samples have image metadata but zero object instances. They are retained as valid data and reported as warnings, not failures or corruption. Nine are in development and two are in holdout.

## Split and reproducibility

- Fixed random seed: **42**
- Selection method: deterministic multi-label proportional-target greedy balancing based on image-level category presence
- Split strategy: a balanced 200-image holdout selected from the chosen 1,000 images; the remaining 800 images form development
- Frozen holdout: all 200 JPEGs are read-only and accompanied by an immutability marker

Release verification reproduced the saved Phase 2 selection assignments exactly. Regenerating `manifests/clean_manifest.json` with `scripts/generate_manifest.py` produced a byte-identical manifest. The regenerated Phase 3 and dataset-validation reports were also byte-identical.

## Validation status

Status: **PASS**

- Validations passed: **13 / 13**
- Validation failures: **0**
- Warnings: **11 valid COCO negative samples detected**
- Missing image files: **0**
- Unreadable or structurally corrupt JPEGs: **0**
- Invalid category IDs: **0**
- Invalid, negative-coordinate, or zero-area bounding boxes: **0**
- Duplicate annotation IDs: **0**
- Manifest summary inconsistencies: **0**
- SHA-256 format or regeneration failures: **0**

The detailed evidence is in `reports/dataset_validation_report.md`.

## Package contents

- `datasets/` — raw COCO acquisition artifacts and the selected clean dataset
- `manifests/` — selection and clean dataset manifests
- `scripts/` — deterministic selection and manifest-generation scripts
- `validators/` — dataset quality validator
- `reports/` — Phase 1 through Phase 4 evidence
- `documentation/` — dataset specification and future attack strategy
- `README.md` — dataset overview and usage references
- `RELEASE_NOTES.md` — this release record
- `SHA256SUMS.txt` — SHA-256 checksums for every packaged file except itself

Python bytecode caches, temporary files, editor artifacts, and operating-system thumbnail files are excluded from the package.

## Known limitations

- This release contains a 1,000-image subset of COCO 2017 validation, not the full COCO dataset.
- Category balancing does not establish broader population or deployment-domain representativeness.
- COCO labels and boxes were not independently relabeled or adjudicated.
- JPEG corruption validation is structural and does not use an independent full pixel decoder.
- Read-only attributes and overwrite guards reduce accidental holdout changes but are not cryptographic access controls.
- No attacked samples or attack-performance metrics are included.

