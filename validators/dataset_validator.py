#!/usr/bin/env python3
"""Validate CV-Assurance-Dataset-v1 without modifying dataset inputs.

The validator always writes a complete PASS/FAIL report. It returns exit code 0
only when every requested validation passes, and exit code 1 when one or more
checks fail. Findings are reported, never repaired.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests" / "clean_manifest.json"
ANNOTATION_PATH = ROOT / "datasets" / "raw" / "annotations" / "instances_val2017.json"
REPORT_PATH = ROOT / "reports" / "dataset_validation_report.md"

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
    canonical = json.dumps(
        sorted(annotations, key=lambda item: int(item["id"])),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def parse_jpeg(data: bytes) -> tuple[int, int]:
    """Strictly validate JPEG container structure and return width/height."""

    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("missing JPEG SOI marker")

    position = 2
    width: int | None = None
    height: int | None = None
    saw_scan = False
    saw_eoi = False

    while position < len(data):
        if data[position] != 0xFF:
            raise ValueError(f"unexpected data outside entropy scan at byte {position}")

        marker_start = position
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            raise ValueError("truncated JPEG marker")

        marker = data[position]
        position += 1
        if marker == 0x00:
            raise ValueError(f"unexpected stuffed byte at byte {marker_start}")
        if marker == 0xD9:
            saw_eoi = True
            break
        if marker in {0x01, 0xD8} or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            raise ValueError("truncated JPEG segment length")

        segment_length = int.from_bytes(data[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(data):
            raise ValueError(f"invalid or truncated JPEG segment at byte {marker_start}")

        if marker in SOF_MARKERS:
            if segment_length < 7:
                raise ValueError("invalid JPEG Start Of Frame segment")
            height = int.from_bytes(data[position + 3 : position + 5], "big")
            width = int.from_bytes(data[position + 5 : position + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError("non-positive JPEG dimensions")

        if marker != 0xDA:
            position += segment_length
            continue

        saw_scan = True
        position += segment_length
        while position < len(data):
            next_marker = data.find(b"\xff", position)
            if next_marker < 0:
                raise ValueError("entropy scan has no terminating marker")
            position = next_marker + 1
            while position < len(data) and data[position] == 0xFF:
                position += 1
            if position >= len(data):
                raise ValueError("truncated marker in entropy scan")
            scan_marker = data[position]
            if scan_marker == 0x00 or 0xD0 <= scan_marker <= 0xD7:
                position += 1
                continue
            position = next_marker
            break

    if not saw_eoi:
        raise ValueError("missing JPEG EOI marker")
    if width is None or height is None:
        raise ValueError("JPEG Start Of Frame segment not found")
    if not saw_scan:
        raise ValueError("JPEG Start Of Scan segment not found")
    if any(byte not in b"\x00\x09\x0a\x0d\x20" for byte in data[position:]):
        raise ValueError("non-whitespace data follows JPEG EOI marker")
    return width, height


def result(name: str, checked: int, issues: list[str], scope: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if not issues else "FAIL",
        "checked": checked,
        "issue_count": len(issues),
        "scope": scope,
        "issues": issues,
    }


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def build_report(
    records: list[dict[str, Any]],
    annotation_count: int,
    validations: list[dict[str, Any]],
    negative_sample_warnings: list[str],
) -> str:
    passed = sum(item["status"] == "PASS" for item in validations)
    failed = len(validations) - passed
    overall = "PASS" if failed == 0 else "FAIL"

    lines = [
        "# Dataset Quality Validation Report",
        "",
        f"## Validation Status: **{overall}**",
        "",
        f"- Clean manifest records: **{len(records)}**",
        f"- Source COCO annotations examined: **{annotation_count}**",
        f"- Validations passed: **{passed} / {len(validations)}**",
        f"- Validations failed: **{failed} / {len(validations)}**",
        f"- Warnings: **{len(negative_sample_warnings)}**",
        "- Dataset inputs modified: **No**",
        "",
        "## Validation results",
        "",
        "| Area | Validation | Result | Checked | Issues |",
        "|---|---|---:|---:|---:|",
    ]

    for item in validations:
        area, name = item["name"].split(" — ", 1)
        lines.append(
            f"| {area} | {name} | **{item['status']}** | "
            f"{item['checked']} | {item['issue_count']} |"
        )

    lines.extend(
        [
            "",
            "## Validation scope and methods",
            "",
            "- Image readability means the complete file could be opened and read without an I/O error.",
            "- Corruption detection uses a strict dependency-free JPEG parser covering SOI/EOI, segment "
            "bounds, Start Of Frame, Start Of Scan, entropy-scan termination, trailing data, and dimension "
            "agreement with the manifest.",
            "- A missing annotation entry means a selected source image ID has no matching COCO image metadata; "
            "this is a failure.",
            "- A selected image with valid COCO image metadata and zero object instances is a valid COCO negative "
            "sample; this is a warning, not corruption and not a validation failure.",
            "- Category and bounding-box checks apply to annotations belonging to the 1,000 selected records.",
            "- Duplicate annotation IDs are checked across the complete source COCO annotation package.",
            "- Image hashes are regenerated from file bytes. Annotation hashes are regenerated from canonical, "
            "annotation-ID-sorted per-image JSON and compared with the clean manifest.",
            "- No error is repaired or suppressed by this validator.",
            "",
            "## Warnings",
            "",
            f"**{len(negative_sample_warnings)} valid COCO negative samples detected.**",
            "",
        ]
    )

    if negative_sample_warnings:
        lines.extend(f"- {warning}" for warning in negative_sample_warnings)
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )

    failures = [item for item in validations if item["issues"]]
    if not failures:
        lines.append("No failures.")
    else:
        for item in failures:
            lines.extend(
                [
                    f"### {item['name']} — {item['status']}",
                    "",
                    f"Scope: {item['scope']}",
                    "",
                ]
            )
            lines.extend(f"- {issue}" for issue in item["issues"])
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Missing clean manifest: {MANIFEST_PATH}")
    if not ANNOTATION_PATH.is_file():
        raise FileNotFoundError(f"Missing COCO annotations: {ANNOTATION_PATH}")

    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    with ANNOTATION_PATH.open("r", encoding="utf-8") as handle:
        annotation_data = json.load(handle)

    if not isinstance(records, list):
        raise TypeError("Clean manifest must be a JSON array")

    metadata_by_id = {int(item["id"]): item for item in annotation_data["images"]}
    categories = {int(item["id"]): str(item["name"]) for item in annotation_data["categories"]}
    annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for annotation in annotation_data["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)

    exists_issues: list[str] = []
    readable_issues: list[str] = []
    corruption_issues: list[str] = []
    image_hash_issues: list[str] = []
    annotation_hash_issues: list[str] = []
    hash_format_issues: list[str] = []
    missing_annotation_issues: list[str] = []
    negative_sample_warnings: list[str] = []
    category_issues: list[str] = []
    bbox_issues: list[str] = []
    negative_coordinate_issues: list[str] = []
    zero_area_issues: list[str] = []
    annotation_consistency_issues: list[str] = []

    selected_annotation_count = 0
    selected_ids: set[int] = set()
    for record in records:
        sample_id = str(record.get("sample_id", "<missing-sample-id>"))
        source_image_id = int(record["source_image_id"])
        selected_ids.add(source_image_id)
        relative_path = str(record["image_path"])
        image_path = ROOT / Path(relative_path)

        image_data: bytes | None = None
        if not image_path.is_file():
            exists_issues.append(f"`{sample_id}`: file does not exist at `{relative_path}`")
        else:
            try:
                image_data = image_path.read_bytes()
            except OSError as error:
                readable_issues.append(f"`{sample_id}`: `{relative_path}` could not be read: {error}")

        if image_data is not None:
            try:
                width, height = parse_jpeg(image_data)
                if width != int(record["image_width"]) or height != int(record["image_height"]):
                    raise ValueError(
                        f"decoded dimensions {width}x{height} do not match manifest "
                        f"{record['image_width']}x{record['image_height']}"
                    )
            except (TypeError, ValueError) as error:
                corruption_issues.append(f"`{sample_id}`: `{relative_path}`: {error}")

            actual_image_hash = hashlib.sha256(image_data).hexdigest()
            if actual_image_hash != record.get("image_sha256"):
                image_hash_issues.append(
                    f"`{sample_id}`: image hash mismatch for `{relative_path}`; "
                    f"manifest `{record.get('image_sha256')}`, actual `{actual_image_hash}`"
                )

        image_hash = record.get("image_sha256")
        annotation_hash = record.get("annotation_sha256")
        if not isinstance(image_hash, str) or len(image_hash) != 64 or any(
            character not in "0123456789abcdef" for character in image_hash
        ):
            hash_format_issues.append(f"`{sample_id}`: invalid `image_sha256` format")
        if not isinstance(annotation_hash, str) or len(annotation_hash) != 64 or any(
            character not in "0123456789abcdef" for character in annotation_hash
        ):
            hash_format_issues.append(f"`{sample_id}`: invalid `annotation_sha256` format")

        image_annotations = sorted(
            annotations_by_image.get(source_image_id, []), key=lambda item: int(item["id"])
        )
        selected_annotation_count += len(image_annotations)
        if source_image_id not in metadata_by_id:
            missing_annotation_issues.append(
                f"`{sample_id}`: source image ID {source_image_id} has no COCO image metadata"
            )
        elif not image_annotations:
            negative_sample_warnings.append(
                f"`{sample_id}` (`{relative_path}`): valid COCO image metadata with zero object instances"
            )

        actual_annotation_hash = canonical_annotation_sha256(image_annotations)
        if actual_annotation_hash != annotation_hash:
            annotation_hash_issues.append(
                f"`{sample_id}`: annotation hash mismatch; manifest `{annotation_hash}`, "
                f"actual `{actual_annotation_hash}`"
            )

        valid_class_ids: set[int] = set()
        actual_bbox_count = 0
        for annotation in image_annotations:
            annotation_id = annotation.get("id", "<missing-id>")
            category_id = annotation.get("category_id")
            if isinstance(category_id, bool) or not isinstance(category_id, int) or category_id not in categories:
                category_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has invalid category ID `{category_id}`"
                )
            else:
                valid_class_ids.add(category_id)

            bbox = annotation.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4 or any(
                isinstance(value, bool) or not isinstance(value, (int, float)) for value in (bbox or [])
            ):
                bbox_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has malformed bbox `{bbox}`"
                )
                continue
            if not all(math.isfinite(float(value)) for value in bbox):
                bbox_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has non-finite bbox `{bbox}`"
                )
                continue

            actual_bbox_count += 1
            x, y, width, height = (float(value) for value in bbox)
            if x < 0 or y < 0:
                negative_coordinate_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has negative origin `{bbox}`"
                )
            if width <= 0 or height <= 0:
                zero_area_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has zero/non-positive area `{bbox}`"
                )
            if width < 0 or height < 0:
                bbox_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` has negative extent `{bbox}`"
                )
            if (
                x + width > float(record["image_width"]) + 1e-6
                or y + height > float(record["image_height"]) + 1e-6
            ):
                bbox_issues.append(
                    f"annotation `{annotation_id}` for `{sample_id}` extends outside "
                    f"{record['image_width']}x{record['image_height']}: `{bbox}`"
                )

        expected_classes = [categories[category_id] for category_id in sorted(valid_class_ids)]
        manifest_classes = record.get("classes_present")
        if (
            int(record.get("object_count", -1)) != len(image_annotations)
            or int(record.get("bbox_count", -1)) != actual_bbox_count
            or manifest_classes != expected_classes
        ):
            annotation_consistency_issues.append(
                f"`{sample_id}`: manifest annotation summary does not match source annotations"
            )

    annotation_ids = [item.get("id") for item in annotation_data["annotations"]]
    duplicate_ids = sorted(
        annotation_id
        for annotation_id, count in Counter(annotation_ids).items()
        if count > 1
    )
    duplicate_id_issues = [
        f"annotation ID `{annotation_id}` occurs more than once in the source annotations"
        for annotation_id in duplicate_ids
    ]

    validations = [
        result("Images — File exists", len(records), exists_issues, "All manifest image paths"),
        result("Images — Readable", len(records), readable_issues, "All existing manifest image files"),
        result(
            "Images — Corrupted image detection",
            len(records),
            corruption_issues,
            "All readable manifest JPEG files",
        ),
        result(
            "Annotations — Missing annotation entry",
            len(records),
            missing_annotation_issues,
            "All selected source image IDs",
        ),
        result(
            "Annotations — Invalid category IDs",
            selected_annotation_count,
            category_issues,
            "Annotations for selected records",
        ),
        result(
            "Annotations — Invalid bounding boxes",
            selected_annotation_count,
            bbox_issues,
            "Annotations for selected records",
        ),
        result(
            "Annotations — Negative coordinates",
            selected_annotation_count,
            negative_coordinate_issues,
            "Bounding boxes for selected records",
        ),
        result(
            "Annotations — Zero-area boxes",
            selected_annotation_count,
            zero_area_issues,
            "Bounding boxes for selected records",
        ),
        result(
            "Annotations — Duplicate annotation IDs",
            len(annotation_ids),
            duplicate_id_issues,
            "Complete COCO source annotation package",
        ),
        result(
            "Annotations — Manifest summary consistency",
            len(records),
            annotation_consistency_issues,
            "Object, bbox, and class summaries in all manifest records",
        ),
        result(
            "Hashes — SHA-256 format",
            len(records) * 2,
            hash_format_issues,
            "Image and annotation hash fields",
        ),
        result(
            "Hashes — Image SHA-256 regeneration",
            len(records),
            image_hash_issues,
            "All readable image files",
        ),
        result(
            "Hashes — Annotation SHA-256 regeneration",
            len(records),
            annotation_hash_issues,
            "Canonical per-image source annotations",
        ),
    ]

    report = build_report(
        records,
        len(annotation_ids),
        validations,
        negative_sample_warnings,
    )
    atomic_write(REPORT_PATH, report)

    failed = [item for item in validations if item["status"] == "FAIL"]
    print(f"Overall: {'FAIL' if failed else 'PASS'}")
    print(f"Validations passed: {len(validations) - len(failed)} / {len(validations)}")
    print(f"Validations failed: {len(failed)} / {len(validations)}")
    print(f"Warnings: {len(negative_sample_warnings)} valid COCO negative samples detected")
    for item in validations:
        print(f"{item['status']}: {item['name']} ({item['issue_count']} issues)")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Validator execution error: {error}", file=sys.stderr)
        raise
