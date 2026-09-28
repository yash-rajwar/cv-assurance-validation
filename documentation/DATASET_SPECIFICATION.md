# CV-Assurance-Dataset-v1 Specification

## 1. Purpose and scope

CV-Assurance-Dataset-v1 is the clean reference dataset for the CV Assurance Validation System. It is a deterministic 1,000-image subset of the official COCO 2017 object-detection validation split.

The dataset currently contains only clean images. Attack generation and attacked derivatives are outside the scope of this specification and are not present in the current dataset.

## 2. Dataset source and version

| Property | Value |
|---|---|
| Source dataset | COCO 2017 Object Detection Dataset |
| Source split | Validation (`val2017`) |
| Source image archive | `http://images.cocodataset.org/zips/val2017.zip` |
| Source annotation archive | `http://images.cocodataset.org/annotations/annotations_trainval2017.zip` |
| Source instance annotations | `datasets/raw/annotations/instances_val2017.json` |
| Source validation images | 5,000 |
| Selected images | 1,000 |

The official annotation archive includes train and validation JSON files. Dataset selection and manifest generation use `instances_val2017.json`; the annotation file is not modified.

## 3. Directory layout

```text
datasets/
|-- raw/
|   |-- images/                         5,000 COCO validation JPEGs
|   |-- annotations/                    official COCO JSON files
|   |-- val2017.zip
|   `-- annotations_trainval2017.zip
`-- coco_clean/
    |-- development/                    800 JPEGs
    `-- holdout/                        200 JPEGs and HOLDOUT_IMMUTABLE.txt

manifests/
|-- image_selection.json
`-- clean_manifest.json

scripts/
|-- phase2_select_and_split.py
`-- generate_manifest.py

validators/
`-- dataset_validator.py
```

## 4. Selection method

Selection is implemented by `scripts/phase2_select_and_split.py`.

The procedure uses image-level category presence rather than raw object-instance counts. For each COCO category, it calculates a target proportional to that category's prevalence in the candidate pool, with a minimum target of one for a category present in the pool. A deterministic greedy procedure selects the candidate that most reduces normalized squared deviation from all category targets. Seeded ranks resolve score ties.

The selection produced:

- 1,000 unique source image IDs
- 1,000 unique filenames
- coverage of all 80 COCO categories in the full selection

### Random seed

The fixed random seed is **42**. It is stored in `manifests/image_selection.json` and defined in the selection script.

## 5. Split strategy

The same proportional-target balancing procedure selects 200 holdout images from the selected 1,000 images. The remaining 800 images are assigned to development.

| Split | Images | Purpose |
|---|---:|---|
| Development | 800 | Development and non-holdout validation work |
| Holdout | 200 | Frozen evaluation subset |

At creation time, both splits contained all 80 COCO categories by image-level presence.

Holdout safeguards are:

- `holdout_immutable.marked` is `true` in `manifests/image_selection.json`.
- `datasets/coco_clean/holdout/HOLDOUT_IMMUTABLE.txt` states the immutability policy.
- All 200 holdout JPEGs and the marker are read-only.
- The Phase 2 script refuses to overwrite an existing clean dataset, selection manifest, or Phase 2 report.

These safeguards protect against accidental changes. They do not constitute cryptographic or operating-system access control.

## 6. Selection manifest

`manifests/image_selection.json` records Phase 2 provenance, selection parameters, class distributions, and the selected images. Each image entry contains:

| Field | Meaning |
|---|---|
| `image_id` | Integer COCO source image ID |
| `filename` | Original COCO JPEG filename |
| `split` | `development` or `holdout` |

## 7. Clean manifest schema

`manifests/clean_manifest.json` is a JSON array with exactly one record per selected image. It is generated from scratch by `scripts/generate_manifest.py`.

| Field | Type | Definition |
|---|---|---|
| `sample_id` | string | Stable identifier formatted as `coco2017-val-` plus the zero-padded COCO image ID |
| `source_dataset` | string | `COCO 2017 Validation` |
| `source_image_id` | integer | COCO source image ID |
| `image_path` | string | Repository-relative clean-image path, including split |
| `image_sha256` | string | Lowercase SHA-256 of the complete JPEG file bytes |
| `annotation_sha256` | string | Lowercase SHA-256 of the canonical per-image COCO annotation list |
| `image_width` | integer | JPEG width verified against COCO image metadata |
| `image_height` | integer | JPEG height verified against COCO image metadata |
| `object_count` | integer | Number of COCO object annotation records for the image |
| `classes_present` | array of strings | Unique COCO category names present, ordered by category ID |
| `bbox_count` | integer | Number of annotation records containing a four-value bounding box |
| `contributor_id` | string | Source-level identifier `coco_2017_official` |
| `status` | string | `CLEAN` for every current record |
| `attack_type` | null | `null` for clean data |
| `parent_id` | null | `null` for clean source samples |

The manifest does not add a separate split field. The split is encoded in `image_path` and remains explicitly recorded in `image_selection.json`.

## 8. Hash methodology

### Image hash

`image_sha256` is generated from the complete bytes of the clean JPEG at `image_path`, read in binary mode. The validator independently regenerates the digest and compares it with the manifest value.

### Annotation hash

For each image, all COCO instance annotation objects belonging to `source_image_id` are:

1. sorted by integer annotation ID;
2. serialized as UTF-8 JSON with object keys sorted;
3. serialized with compact separators and without ASCII-only escaping; and
4. hashed with SHA-256.

For a valid negative sample, the annotation payload is the empty JSON list `[]`; its digest is present and is not treated as a missing hash.

The source `instances_val2017.json` hash is also checked against the Phase 2 provenance hash before clean-manifest generation.

## 9. Validation methodology

Validation is implemented by `validators/dataset_validator.py`. It reports findings and does not repair source data.

### Image checks

- file path exists;
- the complete file is readable;
- JPEG SOI and EOI markers are present;
- JPEG segment boundaries are valid;
- Start Of Frame and Start Of Scan structures are present;
- entropy scans terminate;
- non-whitespace trailing data is absent; and
- parsed dimensions agree with the manifest.

### Annotation checks

- every selected source image ID has a COCO image metadata entry;
- category IDs exist in the COCO category table;
- bounding boxes have four finite numeric values;
- boxes do not extend beyond the recorded image dimensions;
- origins are not negative;
- widths and heights are positive;
- annotation IDs are unique across the complete source instance annotation package; and
- manifest object, bounding-box, and class summaries match source annotations.

### Hash checks

- both digest fields have lowercase 64-character hexadecimal SHA-256 format;
- every image digest is regenerated from image bytes; and
- every annotation digest is regenerated from canonical per-image annotations.

### Current validation result

The current report at `reports/dataset_validation_report.md` records:

- validation status: **PASS**;
- validations passed: **13 / 13**;
- validation failures: **0**; and
- warnings: **11 valid COCO negative samples detected**.

## 10. COCO negative samples

A valid COCO negative sample has a matching entry in the COCO `images` collection but has zero object instances in the COCO `annotations` collection.

CV-Assurance-Dataset-v1 contains 11 such samples: 9 development images and 2 holdout images. They are valid inputs and are retained. They are not classified as missing annotation entries, damaged images, or annotation corruption. The validator reports them as warnings so their presence remains visible.

A selected `source_image_id` with no matching COCO image metadata entry is different: it is a missing annotation linkage and is a validation failure.

## 11. Limitations

- The dataset is limited to 1,000 images sampled from the 5,000-image COCO 2017 validation split.
- The selection procedure targets class diversity and proportional category presence; it does not prove demographic, geographic, environmental, or deployment-domain representativeness.
- Multi-label balancing operates on image-level category presence, not object-instance frequency.
- Eleven images contain zero object instances. They are useful as negative samples but provide no object boxes or class labels.
- Labels and bounding boxes are inherited from COCO and were not independently relabeled or adjudicated in this project.
- Corruption detection performs strict JPEG structural validation but does not use an independent full pixel decoder.
- `contributor_id` is a source-level identifier because individual contributor IDs are not available in the COCO instance annotation records used here.
- Read-only attributes, marker files, and overwrite refusal reduce accidental holdout modification but can be bypassed by an authorized user or process.
- Validation results describe the files at validation time; hashes must be regenerated to detect later changes.
- The current clean manifest contains no attacked samples, so `attack_type` and `parent_id` are `null` for every record.

