# Dataset Quality Validation Report

## Validation Status: **PASS**

- Clean manifest records: **1000**
- Source COCO annotations examined: **36781**
- Validations passed: **13 / 13**
- Validations failed: **0 / 13**
- Warnings: **11**
- Dataset inputs modified: **No**

## Validation results

| Area | Validation | Result | Checked | Issues |
|---|---|---:|---:|---:|
| Images | File exists | **PASS** | 1000 | 0 |
| Images | Readable | **PASS** | 1000 | 0 |
| Images | Corrupted image detection | **PASS** | 1000 | 0 |
| Annotations | Missing annotation entry | **PASS** | 1000 | 0 |
| Annotations | Invalid category IDs | **PASS** | 8890 | 0 |
| Annotations | Invalid bounding boxes | **PASS** | 8890 | 0 |
| Annotations | Negative coordinates | **PASS** | 8890 | 0 |
| Annotations | Zero-area boxes | **PASS** | 8890 | 0 |
| Annotations | Duplicate annotation IDs | **PASS** | 36781 | 0 |
| Annotations | Manifest summary consistency | **PASS** | 1000 | 0 |
| Hashes | SHA-256 format | **PASS** | 2000 | 0 |
| Hashes | Image SHA-256 regeneration | **PASS** | 1000 | 0 |
| Hashes | Annotation SHA-256 regeneration | **PASS** | 1000 | 0 |

## Validation scope and methods

- Image readability means the complete file could be opened and read without an I/O error.
- Corruption detection uses a strict dependency-free JPEG parser covering SOI/EOI, segment bounds, Start Of Frame, Start Of Scan, entropy-scan termination, trailing data, and dimension agreement with the manifest.
- A missing annotation entry means a selected source image ID has no matching COCO image metadata; this is a failure.
- A selected image with valid COCO image metadata and zero object instances is a valid COCO negative sample; this is a warning, not corruption and not a validation failure.
- Category and bounding-box checks apply to annotations belonging to the 1,000 selected records.
- Duplicate annotation IDs are checked across the complete source COCO annotation package.
- Image hashes are regenerated from file bytes. Annotation hashes are regenerated from canonical, annotation-ID-sorted per-image JSON and compared with the clean manifest.
- No error is repaired or suppressed by this validator.

## Warnings

**11 valid COCO negative samples detected.**

- `coco2017-val-000000049091` (`datasets/coco_clean/development/000000049091.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000098497` (`datasets/coco_clean/development/000000098497.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000173183` (`datasets/coco_clean/holdout/000000173183.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000176701` (`datasets/coco_clean/development/000000176701.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000267946` (`datasets/coco_clean/development/000000267946.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000330554` (`datasets/coco_clean/development/000000330554.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000404601` (`datasets/coco_clean/development/000000404601.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000458790` (`datasets/coco_clean/development/000000458790.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000476491` (`datasets/coco_clean/development/000000476491.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000556498` (`datasets/coco_clean/holdout/000000556498.jpg`): valid COCO image metadata with zero object instances
- `coco2017-val-000000560371` (`datasets/coco_clean/development/000000560371.jpg`): valid COCO image metadata with zero object instances

## Findings

No failures.
