#!/usr/bin/env python3
"""Regenerate the CV-Assurance-Dataset-v1 clean manifest from source data.

The output is rebuilt from the frozen Phase 2 selection, the clean image files,
and the unmodified COCO 2017 instance annotations. No existing manifest content
is read or merged.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SELECTION_PATH = ROOT / "manifests" / "image_selection.json"
ANNOTATION_PATH = ROOT / "datasets" / "raw" / "annotations" / "instances_val2017.json"
CLEAN_DATASET_DIR = ROOT / "datasets" / "coco_clean"
OUTPUT_PATH = ROOT / "manifests" / "clean_manifest.json"
REPORT_PATH = ROOT / "reports" / "phase3_manifest_report.md"

SOURCE_DATASET = "COCO 2017 Validation"
CONTRIBUTOR_ID = "coco_2017_official"
EXPECTED_RECORDS = 1000

SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_annotation_sha256(annotations: list[dict[str, Any]]) -> str:
    ordered = sorted(annotations, key=lambda item: int(item["id"]))
    canonical = json.dumps(
        ordered,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def jpeg_dimensions_and_validity(path: Path) -> tuple[int, int]:
    """Validate basic JPEG structure and return width and height.

    This dependency-free validator checks SOI/EOI markers, walks JPEG segments,
    and reads the first Start Of Frame segment. It detects missing, malformed,
    truncated, and dimensionless JPEG files without modifying them.
    """

    data = path.read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("missing JPEG SOI marker")
    if data.rfind(b"\xff\xd9") < 2:
        raise ValueError("missing JPEG EOI marker")

    position = 2
    while position < len(data):
        if data[position] != 0xFF:
            position += 1
            continue

        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            break

        marker = data[position]
        position += 1

        if marker in {0x00, 0x01, 0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            raise ValueError("truncated JPEG segment length")

        segment_length = int.from_bytes(data[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(data):
            raise ValueError("invalid or truncated JPEG segment")

        if marker in SOF_MARKERS:
            if segment_length < 7:
                raise ValueError("invalid JPEG Start Of Frame segment")
            height = int.from_bytes(data[position + 3 : position + 5], "big")
            width = int.from_bytes(data[position + 5 : position + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError("non-positive JPEG dimensions")
            return width, height

        if marker == 0xDA:
            break
        position += segment_length

    raise ValueError("JPEG Start Of Frame segment not found")


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_text_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def build_report(
    records: list[dict[str, Any]],
    invalid_images: list[dict[str, Any]],
    category_count: int,
    represented_category_count: int,
    source_annotation_hash: str,
) -> str:
    missing_image_hashes = sum(not record["image_sha256"] for record in records)
    missing_annotation_hashes = sum(not record["annotation_sha256"] for record in records)
    annotated_records = sum(record["object_count"] > 0 for record in records)
    unannotated_records = len(records) - annotated_records
    object_count = sum(record["object_count"] for record in records)
    bbox_count = sum(record["bbox_count"] for record in records)
    bbox_coverage = 100.0 if object_count == 0 else (bbox_count / object_count) * 100.0
    split_counts = Counter(Path(record["image_path"]).parent.name for record in records)

    lines = [
        "# Phase 3 Clean Manifest Report",
        "",
        "## Summary",
        "",
        f"- Total records: **{len(records)}**",
        f"- Development records: **{split_counts['development']}**",
        f"- Holdout records: **{split_counts['holdout']}**",
        f"- Missing image hashes: **{missing_image_hashes}**",
        f"- Missing annotation hashes: **{missing_annotation_hashes}**",
        f"- Invalid images: **{len(invalid_images)}**",
        "",
        "## Annotation coverage",
        "",
        f"- Records with one or more object annotations: **{annotated_records} / {len(records)}** "
        f"({(annotated_records / len(records)) * 100:.2f}%)",
        f"- Records without object annotations: **{unannotated_records}**",
        f"- Object annotations represented: **{object_count}**",
        f"- Bounding boxes represented: **{bbox_count}**",
        f"- Bounding-box coverage of object annotations: **{bbox_coverage:.2f}%**",
        f"- COCO classes represented: **{represented_category_count} / {category_count}**",
        "",
        "## Hash and validation method",
        "",
        "- `image_sha256` is calculated directly from each clean JPEG file.",
        "- `annotation_sha256` is calculated from the canonical JSON serialization of the complete "
        "COCO annotation list for that image, sorted by annotation ID with sorted object keys.",
        f"- Source annotation SHA-256: `{source_annotation_hash}`",
        "- JPEG validation checks SOI and EOI markers, parses the Start Of Frame dimensions, and "
        "compares those dimensions with the COCO image metadata.",
        "- `contributor_id` is the source-level identifier `coco_2017_official`; individual contributor "
        "identifiers are not present in the COCO instance annotation records.",
        "",
        "## Invalid images",
        "",
    ]

    if invalid_images:
        lines.extend(
            f"- `{item['image_path']}`: {item['reason']}" for item in invalid_images
        )
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Regeneration",
            "",
            "Run from the repository root:",
            "",
            "```powershell",
            "python scripts\\generate_manifest.py",
            "```",
            "",
            "The script reconstructs `manifests/clean_manifest.json` from scratch and atomically "
            "replaces any previous manifest only after all records have been rebuilt.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    if not SELECTION_PATH.is_file():
        raise FileNotFoundError(f"Missing Phase 2 selection manifest: {SELECTION_PATH}")
    if not ANNOTATION_PATH.is_file():
        raise FileNotFoundError(f"Missing COCO annotations: {ANNOTATION_PATH}")

    with SELECTION_PATH.open("r", encoding="utf-8") as handle:
        selection = json.load(handle)
    with ANNOTATION_PATH.open("r", encoding="utf-8") as handle:
        annotation_data = json.load(handle)

    selected_images = selection.get("images", [])
    if len(selected_images) != EXPECTED_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_RECORDS} Phase 2 selections, found {len(selected_images)}"
        )
    if len({int(item["image_id"]) for item in selected_images}) != EXPECTED_RECORDS:
        raise ValueError("Phase 2 selection contains duplicate image IDs")
    if len({item["filename"] for item in selected_images}) != EXPECTED_RECORDS:
        raise ValueError("Phase 2 selection contains duplicate filenames")

    source_annotation_hash = file_sha256(ANNOTATION_PATH)
    selected_source_hash = selection.get("source_annotation_sha256", "").lower()
    if selected_source_hash and selected_source_hash != source_annotation_hash:
        raise ValueError("COCO annotation hash does not match the Phase 2 provenance hash")

    image_metadata = {int(item["id"]): item for item in annotation_data["images"]}
    category_names = {
        int(item["id"]): str(item["name"]) for item in annotation_data["categories"]
    }
    annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for annotation in annotation_data["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)

    records: list[dict[str, Any]] = []
    invalid_images: list[dict[str, Any]] = []
    represented_categories: set[int] = set()

    for selected in sorted(selected_images, key=lambda item: int(item["image_id"])):
        image_id = int(selected["image_id"])
        filename = str(selected["filename"])
        split = str(selected["split"])
        if split not in {"development", "holdout"}:
            raise ValueError(f"Invalid split for image {image_id}: {split}")
        if Path(filename).name != filename:
            raise ValueError(f"Unsafe filename in selection manifest: {filename}")
        if image_id not in image_metadata:
            raise ValueError(f"Image {image_id} is absent from COCO metadata")

        metadata = image_metadata[image_id]
        if metadata["file_name"] != filename:
            raise ValueError(f"Filename mismatch for image {image_id}")

        relative_path = Path("datasets") / "coco_clean" / split / filename
        image_path = ROOT / relative_path
        image_annotations = sorted(
            annotations_by_image.get(image_id, []), key=lambda item: int(item["id"])
        )
        class_ids = sorted({int(item["category_id"]) for item in image_annotations})
        unknown_classes = [category_id for category_id in class_ids if category_id not in category_names]
        if unknown_classes:
            raise ValueError(f"Unknown categories for image {image_id}: {unknown_classes}")
        represented_categories.update(class_ids)

        image_hash = ""
        actual_width = int(metadata["width"])
        actual_height = int(metadata["height"])
        if not image_path.is_file():
            invalid_images.append(
                {"image_path": relative_path.as_posix(), "reason": "file is missing"}
            )
        else:
            image_hash = file_sha256(image_path)
            try:
                actual_width, actual_height = jpeg_dimensions_and_validity(image_path)
                if (
                    actual_width != int(metadata["width"])
                    or actual_height != int(metadata["height"])
                ):
                    raise ValueError(
                        "JPEG dimensions "
                        f"{actual_width}x{actual_height} do not match COCO metadata "
                        f"{metadata['width']}x{metadata['height']}"
                    )
            except (OSError, ValueError) as error:
                invalid_images.append(
                    {"image_path": relative_path.as_posix(), "reason": str(error)}
                )

        bbox_count = sum(
            isinstance(item.get("bbox"), list) and len(item["bbox"]) == 4
            for item in image_annotations
        )
        records.append(
            {
                "sample_id": f"coco2017-val-{image_id:012d}",
                "source_dataset": SOURCE_DATASET,
                "source_image_id": image_id,
                "image_path": relative_path.as_posix(),
                "image_sha256": image_hash,
                "annotation_sha256": canonical_annotation_sha256(image_annotations),
                "image_width": actual_width,
                "image_height": actual_height,
                "object_count": len(image_annotations),
                "classes_present": [category_names[category_id] for category_id in class_ids],
                "bbox_count": bbox_count,
                "contributor_id": CONTRIBUTOR_ID,
                "status": "CLEAN",
                "attack_type": None,
                "parent_id": None,
            }
        )

    report = build_report(
        records,
        invalid_images,
        len(category_names),
        len(represented_categories),
        source_annotation_hash,
    )
    atomic_text_write(REPORT_PATH, report)

    missing_hashes = sum(
        not record["image_sha256"] or not record["annotation_sha256"] for record in records
    )
    if invalid_images or missing_hashes:
        raise RuntimeError(
            f"Manifest validation failed: {len(invalid_images)} invalid images, "
            f"{missing_hashes} records with missing hashes. See {REPORT_PATH}."
        )
    if len(records) != EXPECTED_RECORDS:
        raise AssertionError("Clean manifest record count is not 1,000")
    if any(
        record["status"] != "CLEAN"
        or record["attack_type"] is not None
        or record["parent_id"] is not None
        for record in records
    ):
        raise AssertionError("Clean-record state fields are invalid")

    atomic_json_write(OUTPUT_PATH, records)
    print(f"Records: {len(records)}")
    print("Missing hashes: 0")
    print("Invalid images: 0")
    print(f"Annotated records: {sum(item['object_count'] > 0 for item in records)}")
    print(f"Classes represented: {len(represented_categories)} / {len(category_names)}")
    print(f"Manifest: {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
