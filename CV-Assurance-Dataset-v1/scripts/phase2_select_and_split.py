#!/usr/bin/env python3
"""Create the reproducible CV-Assurance-Dataset-v1 clean split.

The script intentionally refuses to overwrite an existing clean dataset,
manifest, or Phase 2 report so a frozen holdout cannot be changed by rerunning
the pipeline in place.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import stat
from collections import Counter, defaultdict
from pathlib import Path


SEED = 42
SELECTED_COUNT = 1000
DEVELOPMENT_COUNT = 800
HOLDOUT_COUNT = 200
EMPTY_LABEL = -1

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_PATH = ROOT / "datasets" / "raw" / "annotations" / "instances_val2017.json"
RAW_IMAGE_DIR = ROOT / "datasets" / "raw" / "images"
CLEAN_DIR = ROOT / "datasets" / "coco_clean"
DEVELOPMENT_DIR = CLEAN_DIR / "development"
HOLDOUT_DIR = CLEAN_DIR / "holdout"
MANIFEST_PATH = ROOT / "manifests" / "image_selection.json"
REPORT_PATH = ROOT / "reports" / "phase2_split_report.md"
HOLDOUT_MARKER = HOLDOUT_DIR / "HOLDOUT_IMMUTABLE.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def labels_for_images(annotation_data: dict) -> dict[int, tuple[int, ...]]:
    labels: dict[int, set[int]] = defaultdict(set)
    for annotation in annotation_data["annotations"]:
        labels[int(annotation["image_id"])].add(int(annotation["category_id"]))

    result: dict[int, tuple[int, ...]] = {}
    for image in annotation_data["images"]:
        image_id = int(image["id"])
        image_labels = labels.get(image_id)
        result[image_id] = tuple(sorted(image_labels)) if image_labels else (EMPTY_LABEL,)
    return result


def proportional_targets(
    pool_ids: list[int], sample_size: int, image_labels: dict[int, tuple[int, ...]]
) -> dict[int, int]:
    prevalence: Counter[int] = Counter()
    for image_id in pool_ids:
        prevalence.update(image_labels[image_id])

    ratio = sample_size / len(pool_ids)
    return {
        label: max(1, round(count * ratio))
        for label, count in prevalence.items()
        if count > 0
    }


def balanced_sample(
    pool_ids: list[int], sample_size: int, image_labels: dict[int, tuple[int, ...]], seed: int
) -> tuple[list[int], dict[int, int]]:
    """Greedily minimize normalized squared class-target error.

    Image-level category presence is used rather than instance counts so a
    single crowded image cannot dominate selection. Seeded ranks resolve all
    score ties, making the result reproducible.
    """

    if sample_size > len(pool_ids):
        raise ValueError("Sample size exceeds the candidate pool")

    targets = proportional_targets(pool_ids, sample_size, image_labels)
    ranked_ids = list(pool_ids)
    random.Random(seed).shuffle(ranked_ids)
    tie_rank = {image_id: rank for rank, image_id in enumerate(ranked_ids)}

    remaining = set(pool_ids)
    selected: list[int] = []
    current: Counter[int] = Counter()

    def candidate_score(image_id: int) -> tuple[float, int]:
        improvement = 0.0
        for label in image_labels[image_id]:
            target = targets[label]
            before = (target - current[label]) / target
            after = (target - (current[label] + 1)) / target
            improvement += before * before - after * after
        return (round(improvement, 15), -tie_rank[image_id])

    for _ in range(sample_size):
        chosen = max(remaining, key=candidate_score)
        remaining.remove(chosen)
        selected.append(chosen)
        current.update(image_labels[chosen])

    return selected, targets


def class_presence(
    image_ids: set[int], image_labels: dict[int, tuple[int, ...]], category_ids: list[int]
) -> dict[int, int]:
    counts = {category_id: 0 for category_id in category_ids}
    for image_id in image_ids:
        for category_id in image_labels[image_id]:
            if category_id != EMPTY_LABEL:
                counts[category_id] += 1
    return counts


def ensure_fresh_outputs() -> None:
    conflicts = [path for path in (CLEAN_DIR, MANIFEST_PATH, REPORT_PATH) if path.exists()]
    if conflicts:
        joined = ", ".join(str(path.relative_to(ROOT)) for path in conflicts)
        raise FileExistsError(
            f"Refusing to overwrite existing Phase 2 artifacts: {joined}. "
            "This protects the frozen holdout."
        )


def make_report(
    categories: list[dict],
    source_counts: dict[int, int],
    selected_counts: dict[int, int],
    development_counts: dict[int, int],
    holdout_counts: dict[int, int],
    annotation_hash: str,
) -> str:
    lines = [
        "# Phase 2 Dataset Selection and Split Report",
        "",
        "## Summary",
        "",
        "- Dataset: `CV-Assurance-Dataset-v1`",
        "- Source: COCO 2017 validation images and `instances_val2017.json`",
        f"- Total selected images: **{SELECTED_COUNT}**",
        f"- Development images: **{DEVELOPMENT_COUNT}**",
        f"- Frozen holdout images: **{HOLDOUT_COUNT}**",
        f"- Fixed random seed: **{SEED}**",
        f"- Source annotation SHA-256: `{annotation_hash}`",
        "",
        "## Reproducible selection method",
        "",
        "Selection uses image-level category presence from the unmodified COCO instance annotations. "
        "For each category, a target is calculated from its proportional prevalence in the candidate "
        "pool, with a minimum target of one for rare categories. A deterministic greedy procedure "
        "selects the image that most reduces normalized squared deviation from all category targets; "
        "seeded ranks resolve ties. The same method selects the 200-image holdout from the selected "
        "1,000 images, and the remaining 800 images form the development split.",
        "",
        "The complete procedure is saved in `scripts/phase2_select_and_split.py`.",
        "",
        "## Holdout immutability",
        "",
        "The holdout is marked immutable in `manifests/image_selection.json`, has a "
        "`datasets/coco_clean/holdout/HOLDOUT_IMMUTABLE.txt` policy marker, and all 200 holdout JPEG "
        "files plus the marker are set read-only. The generation script refuses to overwrite any "
        "existing Phase 2 dataset, manifest, or report.",
        "",
        "## Class distribution",
        "",
        "Counts below represent images containing each class, not the number of object instances. "
        "An image can contribute to multiple rows.",
        "",
        "| ID | Class | COCO val (5,000) | Selected (1,000) | Development (800) | Holdout (200) |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for category in sorted(categories, key=lambda item: int(item["id"])):
        category_id = int(category["id"])
        name = str(category["name"]).replace("|", "\\|")
        lines.append(
            f"| {category_id} | {name} | {source_counts[category_id]} | "
            f"{selected_counts[category_id]} | {development_counts[category_id]} | "
            f"{holdout_counts[category_id]} |"
        )

    lines.extend(
        [
            "",
            "## Verification",
            "",
            f"- Selected images: **{SELECTED_COUNT}**",
            f"- Development directory JPEGs: **{DEVELOPMENT_COUNT}**",
            f"- Holdout directory JPEGs: **{HOLDOUT_COUNT}**",
            f"- Manifest entries: **{SELECTED_COUNT}**",
            "- All 80 COCO categories are represented in the selected dataset.",
            "- All 80 COCO categories are represented in the development split.",
            "- All 80 COCO categories are represented in the holdout split.",
            "- Source annotations were hash-checked before and after processing and were not modified.",
            "- No attacks were created.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ensure_fresh_outputs()
    if not ANNOTATION_PATH.is_file() or not RAW_IMAGE_DIR.is_dir():
        raise FileNotFoundError("Required Phase 1 image or annotation input is missing")

    annotation_hash_before = sha256(ANNOTATION_PATH)
    with ANNOTATION_PATH.open("r", encoding="utf-8") as handle:
        annotation_data = json.load(handle)

    images = {int(item["id"]): item for item in annotation_data["images"]}
    all_ids = sorted(images)
    if len(all_ids) != 5000:
        raise ValueError(f"Expected 5,000 COCO validation images, found {len(all_ids)}")

    missing_images = [
        images[image_id]["file_name"]
        for image_id in all_ids
        if not (RAW_IMAGE_DIR / images[image_id]["file_name"]).is_file()
    ]
    if missing_images:
        raise FileNotFoundError(f"Missing {len(missing_images)} source image files")

    image_labels = labels_for_images(annotation_data)
    selected_order, selection_targets = balanced_sample(all_ids, SELECTED_COUNT, image_labels, SEED)
    selected_ids = set(selected_order)
    holdout_order, holdout_targets = balanced_sample(
        sorted(selected_ids), HOLDOUT_COUNT, image_labels, SEED
    )
    holdout_ids = set(holdout_order)
    development_ids = selected_ids - holdout_ids

    if len(selected_ids) != SELECTED_COUNT:
        raise AssertionError("Selected image count is not 1,000")
    if len(development_ids) != DEVELOPMENT_COUNT or len(holdout_ids) != HOLDOUT_COUNT:
        raise AssertionError("Development/holdout split count is invalid")
    if development_ids & holdout_ids:
        raise AssertionError("Development and holdout splits overlap")

    category_ids = sorted(int(category["id"]) for category in annotation_data["categories"])
    source_counts = class_presence(set(all_ids), image_labels, category_ids)
    selected_counts = class_presence(selected_ids, image_labels, category_ids)
    development_counts = class_presence(development_ids, image_labels, category_ids)
    holdout_counts = class_presence(holdout_ids, image_labels, category_ids)

    for split_name, counts in (
        ("selected", selected_counts),
        ("development", development_counts),
        ("holdout", holdout_counts),
    ):
        absent = [category_id for category_id, count in counts.items() if count == 0]
        if absent:
            raise AssertionError(f"Categories absent from {split_name}: {absent}")

    DEVELOPMENT_DIR.mkdir(parents=True)
    HOLDOUT_DIR.mkdir(parents=True)
    for image_id in sorted(development_ids):
        filename = images[image_id]["file_name"]
        shutil.copy2(RAW_IMAGE_DIR / filename, DEVELOPMENT_DIR / filename)
    for image_id in sorted(holdout_ids):
        filename = images[image_id]["file_name"]
        shutil.copy2(RAW_IMAGE_DIR / filename, HOLDOUT_DIR / filename)

    HOLDOUT_MARKER.write_text(
        "CV-Assurance-Dataset-v1 frozen holdout\n"
        "Created by scripts/phase2_select_and_split.py with seed 42.\n"
        "Do not add, remove, rename, replace, or modify files in this directory.\n",
        encoding="utf-8",
    )

    manifest_entries = []
    for image_id in sorted(selected_ids):
        manifest_entries.append(
            {
                "image_id": image_id,
                "filename": images[image_id]["file_name"],
                "split": "holdout" if image_id in holdout_ids else "development",
            }
        )

    manifest = {
        "dataset_name": "CV-Assurance-Dataset-v1",
        "source_dataset": "COCO 2017 validation",
        "source_annotation": "datasets/raw/annotations/instances_val2017.json",
        "source_annotation_sha256": annotation_hash_before,
        "random_seed": SEED,
        "selection_method": "deterministic multi-label proportional-target greedy balancing",
        "counts": {
            "selected": SELECTED_COUNT,
            "development": DEVELOPMENT_COUNT,
            "holdout": HOLDOUT_COUNT,
        },
        "holdout_immutable": {
            "marked": True,
            "marker_file": "datasets/coco_clean/holdout/HOLDOUT_IMMUTABLE.txt",
            "image_files_read_only": True,
            "policy": "Never modify holdout data after creation.",
        },
        "selection_targets_by_category_id": {
            str(key): value for key, value in sorted(selection_targets.items()) if key != EMPTY_LABEL
        },
        "holdout_targets_by_category_id": {
            str(key): value for key, value in sorted(holdout_targets.items()) if key != EMPTY_LABEL
        },
        "class_distribution": {
            str(category_id): {
                "source": source_counts[category_id],
                "selected": selected_counts[category_id],
                "development": development_counts[category_id],
                "holdout": holdout_counts[category_id],
            }
            for category_id in category_ids
        },
        "images": manifest_entries,
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = make_report(
        annotation_data["categories"],
        source_counts,
        selected_counts,
        development_counts,
        holdout_counts,
        annotation_hash_before,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    annotation_hash_after = sha256(ANNOTATION_PATH)
    if annotation_hash_before != annotation_hash_after:
        raise AssertionError("Source annotation file changed during processing")

    for image_id in holdout_ids:
        os.chmod(HOLDOUT_DIR / images[image_id]["file_name"], stat.S_IREAD)
    os.chmod(HOLDOUT_MARKER, stat.S_IREAD)

    development_jpegs = list(DEVELOPMENT_DIR.glob("*.jpg"))
    holdout_jpegs = list(HOLDOUT_DIR.glob("*.jpg"))
    read_only_holdout = sum(not (path.stat().st_mode & stat.S_IWRITE) for path in holdout_jpegs)
    if len(development_jpegs) != DEVELOPMENT_COUNT:
        raise AssertionError("Development directory verification failed")
    if len(holdout_jpegs) != HOLDOUT_COUNT or read_only_holdout != HOLDOUT_COUNT:
        raise AssertionError("Holdout directory or read-only verification failed")

    print(f"Selected: {len(selected_ids)}")
    print(f"Development: {len(development_jpegs)}")
    print(f"Holdout: {len(holdout_jpegs)}")
    print(f"Read-only holdout JPEGs: {read_only_holdout}")
    print(f"Manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
