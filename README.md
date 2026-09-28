# CV-Assurance-Dataset-v1

CV-Assurance-Dataset-v1 is a reproducible 1,000-image clean dataset derived from the official COCO 2017 validation split for computer-vision assurance work. It contains 800 development images and a frozen 200-image holdout.

This repository is a validation environment, not the production application. The current dataset contains clean images only; no attacks are included.

## Dataset source

- Source dataset: COCO 2017 Object Detection validation split
- Validation images: `http://images.cocodataset.org/zips/val2017.zip`
- Train/validation annotations: `http://images.cocodataset.org/annotations/annotations_trainval2017.zip`
- Source image pool: 5,000 COCO validation JPEGs
- Source instance annotation file: `datasets/raw/annotations/instances_val2017.json`

The original archives and extracted raw data are retained beneath `datasets/raw/`.

## Clean dataset

```text
datasets/coco_clean/
|-- development/    800 JPEGs
`-- holdout/        200 read-only JPEGs plus an immutability marker
```

Selection used fixed random seed `42` and deterministic multi-label proportional-target balancing based on image-level COCO category presence. The same balancing method selected the 200-image holdout from the chosen 1,000 images; the other 800 images form the development split.

The holdout is marked immutable in the selection manifest, has a `HOLDOUT_IMMUTABLE.txt` marker, and its JPEGs are read-only. The Phase 2 generator refuses to overwrite an existing clean dataset or split.

## Manifests

- `manifests/image_selection.json` records the 1,000 source image IDs, filenames, and split assignments.
- `manifests/clean_manifest.json` contains one provenance and integrity record per selected image.

The clean manifest is regenerated from source data with:

```powershell
python scripts\generate_manifest.py
```

See [DATASET_SPECIFICATION.md](documentation/DATASET_SPECIFICATION.md) for the complete schema and hash definitions.

## Validation status

Dataset quality validation currently reports **PASS**:

- 13 of 13 validations passed.
- Image existence, readability, JPEG structure, categories, bounding boxes, annotation IDs, manifest summaries, and regenerated hashes passed.
- 11 valid COCO negative samples were reported as warnings: 9 in development and 2 in holdout.

A COCO negative sample has a valid COCO image metadata entry but zero object instances. It is valid data, not a missing annotation entry and not image corruption. A selected source image ID with no matching COCO image metadata remains a validation failure.

Run validation with:

```powershell
python validators\dataset_validator.py
```

The detailed result is in [dataset_validation_report.md](reports/dataset_validation_report.md).

## Project artifacts

- `scripts/phase2_select_and_split.py` — deterministic image selection and split creation
- `scripts/generate_manifest.py` — clean-manifest regeneration
- `validators/dataset_validator.py` — non-mutating dataset quality validation
- `reports/phase1_dataset_acquisition_report.md` — acquisition evidence
- `reports/phase2_split_report.md` — split method and class distribution
- `reports/phase3_manifest_report.md` — manifest coverage and integrity results
- `reports/dataset_validation_report.md` — current quality-validation results

## Limitations

- This is a 1,000-image subset of COCO 2017 validation, not the full COCO dataset.
- Diversity balancing preserves category coverage but does not establish population representativeness or equal class frequency.
- Eleven selected images contain no object instances; these are retained valid negative samples.
- COCO annotations are inherited without relabeling or independent ground-truth review.
- JPEG corruption validation is structural and does not use an independent full pixel decoder.
- Read-only holdout attributes and overwrite guards reduce accidental modification but are not cryptographic access controls.
- `contributor_id` identifies the official COCO 2017 source, not an individual image contributor.

