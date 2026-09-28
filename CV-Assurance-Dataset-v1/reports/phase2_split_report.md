# Phase 2 Dataset Selection and Split Report

## Summary

- Dataset: `CV-Assurance-Dataset-v1`
- Source: COCO 2017 validation images and `instances_val2017.json`
- Total selected images: **1000**
- Development images: **800**
- Frozen holdout images: **200**
- Fixed random seed: **42**
- Source annotation SHA-256: `E8C7F7908F1D7278341FAE127D0DA654F102F11BD7B21D8AEEFA635B8C810B6F`

## Reproducible selection method

Selection uses image-level category presence from the unmodified COCO instance annotations. For each category, a target is calculated from its proportional prevalence in the candidate pool, with a minimum target of one for rare categories. A deterministic greedy procedure selects the image that most reduces normalized squared deviation from all category targets; seeded ranks resolve ties. The same method selects the 200-image holdout from the selected 1,000 images, and the remaining 800 images form the development split.

The complete procedure is saved in `scripts/phase2_select_and_split.py`.

## Holdout immutability

The holdout is marked immutable in `manifests/image_selection.json`, has a `datasets/coco_clean/holdout/HOLDOUT_IMMUTABLE.txt` policy marker, and all 200 holdout JPEG files plus the marker are set read-only. The generation script refuses to overwrite any existing Phase 2 dataset, manifest, or report.

## Class distribution

Counts below represent images containing each class, not the number of object instances. An image can contribute to multiple rows.

| ID | Class | COCO val (5,000) | Selected (1,000) | Development (800) | Holdout (200) |
|---:|---|---:|---:|---:|---:|
| 1 | person | 2693 | 586 | 464 | 122 |
| 2 | bicycle | 149 | 38 | 29 | 9 |
| 3 | car | 535 | 122 | 89 | 33 |
| 4 | motorcycle | 159 | 41 | 32 | 9 |
| 5 | airplane | 97 | 22 | 18 | 4 |
| 6 | bus | 189 | 51 | 40 | 11 |
| 7 | train | 157 | 39 | 30 | 9 |
| 8 | truck | 250 | 71 | 54 | 17 |
| 9 | boat | 121 | 29 | 22 | 7 |
| 10 | traffic light | 191 | 51 | 39 | 12 |
| 11 | fire hydrant | 86 | 20 | 16 | 4 |
| 13 | stop sign | 69 | 16 | 13 | 3 |
| 14 | parking meter | 37 | 7 | 6 | 1 |
| 15 | bench | 235 | 66 | 50 | 16 |
| 16 | bird | 125 | 30 | 23 | 7 |
| 17 | cat | 184 | 49 | 37 | 12 |
| 18 | dog | 177 | 46 | 36 | 10 |
| 19 | horse | 128 | 32 | 25 | 7 |
| 20 | sheep | 65 | 14 | 11 | 3 |
| 21 | cow | 87 | 20 | 16 | 4 |
| 22 | elephant | 89 | 21 | 17 | 4 |
| 23 | bear | 49 | 11 | 9 | 2 |
| 24 | zebra | 85 | 20 | 16 | 4 |
| 25 | giraffe | 101 | 23 | 18 | 5 |
| 27 | backpack | 228 | 53 | 39 | 14 |
| 28 | umbrella | 174 | 46 | 36 | 10 |
| 31 | handbag | 292 | 62 | 48 | 14 |
| 32 | tie | 145 | 36 | 28 | 8 |
| 33 | suitcase | 105 | 25 | 20 | 5 |
| 34 | frisbee | 84 | 19 | 15 | 4 |
| 35 | skis | 120 | 29 | 22 | 7 |
| 36 | snowboard | 49 | 11 | 9 | 2 |
| 37 | sports ball | 169 | 44 | 34 | 10 |
| 38 | kite | 91 | 21 | 17 | 4 |
| 39 | baseball bat | 97 | 22 | 18 | 4 |
| 40 | baseball glove | 100 | 23 | 18 | 5 |
| 41 | skateboard | 127 | 30 | 23 | 7 |
| 42 | surfboard | 149 | 38 | 29 | 9 |
| 43 | tennis racket | 167 | 42 | 33 | 9 |
| 44 | bottle | 379 | 89 | 66 | 23 |
| 46 | wine glass | 110 | 26 | 21 | 5 |
| 47 | cup | 390 | 88 | 68 | 20 |
| 48 | fork | 155 | 35 | 27 | 8 |
| 49 | knife | 181 | 40 | 31 | 9 |
| 50 | spoon | 153 | 38 | 29 | 9 |
| 51 | bowl | 314 | 70 | 54 | 16 |
| 52 | banana | 103 | 25 | 20 | 5 |
| 53 | apple | 76 | 17 | 14 | 3 |
| 54 | sandwich | 98 | 23 | 18 | 5 |
| 55 | orange | 85 | 20 | 16 | 4 |
| 56 | broccoli | 71 | 16 | 13 | 3 |
| 57 | carrot | 81 | 18 | 14 | 4 |
| 58 | hot dog | 51 | 11 | 9 | 2 |
| 59 | pizza | 153 | 39 | 30 | 9 |
| 60 | donut | 62 | 13 | 10 | 3 |
| 61 | cake | 124 | 30 | 23 | 7 |
| 62 | chair | 580 | 134 | 102 | 32 |
| 63 | couch | 195 | 44 | 35 | 9 |
| 64 | potted plant | 172 | 38 | 29 | 9 |
| 65 | bed | 149 | 38 | 29 | 9 |
| 67 | dining table | 501 | 110 | 85 | 25 |
| 70 | toilet | 149 | 38 | 29 | 9 |
| 72 | tv | 207 | 48 | 37 | 11 |
| 73 | laptop | 183 | 45 | 35 | 10 |
| 74 | mouse | 88 | 19 | 15 | 4 |
| 75 | remote | 145 | 36 | 28 | 8 |
| 76 | keyboard | 106 | 23 | 18 | 5 |
| 77 | cell phone | 214 | 59 | 45 | 14 |
| 78 | microwave | 54 | 12 | 10 | 2 |
| 79 | oven | 115 | 27 | 22 | 5 |
| 80 | toaster | 8 | 2 | 1 | 1 |
| 81 | sink | 187 | 49 | 37 | 12 |
| 82 | refrigerator | 101 | 23 | 18 | 5 |
| 84 | book | 230 | 50 | 40 | 10 |
| 85 | clock | 204 | 56 | 43 | 13 |
| 86 | vase | 137 | 33 | 25 | 8 |
| 87 | scissors | 28 | 6 | 5 | 1 |
| 88 | teddy bear | 94 | 22 | 18 | 4 |
| 89 | hair drier | 9 | 2 | 1 | 1 |
| 90 | toothbrush | 34 | 7 | 6 | 1 |

## Verification

- Selected images: **1000**
- Development directory JPEGs: **800**
- Holdout directory JPEGs: **200**
- Manifest entries: **1000**
- All 80 COCO categories are represented in the selected dataset.
- All 80 COCO categories are represented in the development split.
- All 80 COCO categories are represented in the holdout split.
- Source annotations were hash-checked before and after processing and were not modified.
- No attacks were created.
