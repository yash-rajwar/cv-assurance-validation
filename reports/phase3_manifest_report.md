# Phase 3 Clean Manifest Report

## Summary

- Total records: **1000**
- Development records: **800**
- Holdout records: **200**
- Missing image hashes: **0**
- Missing annotation hashes: **0**
- Invalid images: **0**

## Annotation coverage

- Records with one or more object annotations: **989 / 1000** (98.90%)
- Records without object annotations: **11**
- Object annotations represented: **8890**
- Bounding boxes represented: **8890**
- Bounding-box coverage of object annotations: **100.00%**
- COCO classes represented: **80 / 80**

## Hash and validation method

- `image_sha256` is calculated directly from each clean JPEG file.
- `annotation_sha256` is calculated from the canonical JSON serialization of the complete COCO annotation list for that image, sorted by annotation ID with sorted object keys.
- Source annotation SHA-256: `e8c7f7908f1d7278341fae127d0da654f102f11bd7b21d8aeefa635b8c810b6f`
- JPEG validation checks SOI and EOI markers, parses the Start Of Frame dimensions, and compares those dimensions with the COCO image metadata.
- `contributor_id` is the source-level identifier `coco_2017_official`; individual contributor identifiers are not present in the COCO instance annotation records.

## Invalid images

None.

## Regeneration

Run from the repository root:

```powershell
python scripts\generate_manifest.py
```

The script reconstructs `manifests/clean_manifest.json` from scratch and atomically replaces any previous manifest only after all records have been rebuilt.
