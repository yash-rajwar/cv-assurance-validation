# Attack Simulation Framework Plan

## Status

This document is a plan for future work. The `attack_generators/` tree currently contains documentation-only placeholders. No attack code, attacked images, attacked annotations, attack manifests, or attack metrics have been generated.

## Purpose

The future framework will create controlled dataset-integrity test cases derived from approved inputs. Its purpose will be to evaluate whether assurance checks detect known, documented changes while preserving an auditable relationship to the clean dataset.

The plan covers six attack families:

1. isolated label flips;
2. systematic mislabeling;
3. duplicate records or submissions;
4. out-of-distribution inputs;
5. visual triggers; and
6. contributor-associated anomalies.

## Non-negotiable safeguards

- Never modify files in `datasets/coco_clean/` in place.
- Never modify the raw COCO images or annotation package.
- Never modify the frozen holdout split.
- Use development samples only unless a later approved protocol explicitly defines another non-mutating evaluation source.
- Create attacked artifacts in a separate output location that is not part of the clean dataset.
- Use fixed, recorded seeds for every randomized operation.
- Preserve reproducible parameters and complete parent provenance.
- Recompute hashes after every intentional image or annotation change.
- Report generation or validation errors; do not repair or exclude them silently.
- Do not report performance or security conclusions until evaluation evidence exists.

## Planned common workflow

Each future generator should follow the same staged process:

1. **Configuration** — Load a versioned attack configuration containing the attack type, parameters, fixed seed, requested sample count, and eligibility rules.
2. **Eligibility** — Resolve eligible clean development records from `manifests/clean_manifest.json`. Reject holdout paths and records that do not satisfy attack-specific prerequisites.
3. **Deterministic selection** — Select parents with the configured seed and a stable ordering rule. Save the selected parent IDs before transformation.
4. **Copy and transform** — Copy required inputs into an isolated attack output location and apply the requested transformation only to the copies.
5. **Manifest creation** — Create a separate attacked-data manifest. Every derived sample must have a unique sample ID, an attack type, a non-null parent ID when it derives from a clean sample, updated hashes, and recorded parameters.
6. **Validation** — Verify counts, paths, hashes, parent existence, split isolation, image integrity, and annotation validity. Apply attack-specific assertions that confirm the intended change occurred.
7. **Reporting** — Write a report containing the configuration, seed, affected records, validation outcomes, failures, and warnings. Metrics must come from an actual evaluation run and must not be fabricated.

No future generator should publish partial output as complete. Generation should use temporary output and finalize the artifact only after validation succeeds.

## Planned provenance and identity rules

The clean manifest is the source of parent identity and integrity evidence. Future attacked records should retain the clean schema where applicable and use these planned conventions:

| Field | Planned attacked-record behavior |
|---|---|
| `sample_id` | New deterministic identifier unique to the attacked artifact |
| `source_dataset` | Preserve the original source when derived from COCO; record the actual source for external OOD data |
| `source_image_id` | Preserve for a derived COCO sample; use a source-appropriate identifier for external data |
| `image_path` | Point only to the isolated attacked copy |
| `image_sha256` | Recompute from final attacked image bytes; retain the clean value only for exact-byte duplicates |
| `annotation_sha256` | Recompute from final attacked annotations |
| `contributor_id` | Preserve source provenance or use an explicitly synthetic attack contributor identifier |
| `status` | Use an attacked-state value defined by the future manifest specification |
| `attack_type` | Non-null canonical attack-family identifier |
| `parent_id` | Clean parent `sample_id` for derived samples; external OOD handling must be explicitly defined |

The attacked-manifest schema and allowed `status` and `attack_type` values must be finalized before implementation. This plan does not claim that those extensions currently exist.

## Attack-family strategies

### 1. Label flip

The isolated label-flip generator will target individual annotations in a deterministic subset and replace each selected category with a different valid COCO category. It should preserve image bytes and bounding-box geometry unless a later configuration explicitly states otherwise.

Required future parameters include parent selection count or rate, annotation selection rule, replacement-category rule, and seed. Validation must prove that only the intended category fields changed and that all resulting category IDs remain valid.

### 2. Systematic mislabel

The systematic-mislabel generator will apply a documented category mapping consistently across all eligible annotations in the selected scope. This differs from isolated label flips because the mapping is rule-based and repeated across samples.

The mapping must be versioned, contain valid non-identity source/target pairs, and define behavior for images containing multiple affected classes. Validation must compare observed changes with the configured mapping.

### 3. Duplicate

The duplicate generator will create explicitly tracked repeated records or file copies from deterministic clean parents. It may support exact-byte duplicates and, if later approved, metadata-level duplicate scenarios.

Every duplicate must receive a unique attacked sample ID and a clean parent ID. Validation must confirm the expected duplicate groups, multiplicities, file hashes, and absence of sample-ID collisions.

### 4. Out-of-distribution

The OOD generator or acquisition process cannot be implemented until the intended distribution boundary and data source are defined. Future configuration must state why a source is considered out of distribution relative to this COCO-derived dataset.

External data must include source and version information, acquisition date, provenance, usage constraints, and preprocessing history. External OOD records must not be presented as COCO-derived samples when no COCO parent exists.

### 5. Trigger

The trigger generator will apply a specified visual pattern to copies of development images. The trigger specification must include content, geometry, placement, opacity, color handling, clipping behavior, and any randomized parameters.

Validation must confirm source files are unchanged, output dimensions remain as configured, intended pixels changed, generated images remain structurally valid, and hashes differ from parents when pixels change.

### 6. Contributor

The contributor generator will model anomalies associated with synthetic contributor groups or source-group metadata. It must not attribute malicious behavior to real COCO contributors.

Future scenarios may combine an explicitly synthetic contributor ID with another controlled corruption, but the relationship and affected scope must be recorded. Validation must confirm grouping logic, provenance, attack parameters, and holdout isolation.

## Reproducibility requirements

Each future attack run should record at least:

- generator name and version;
- attack-family identifier;
- complete configuration;
- fixed random seed;
- clean-manifest hash;
- selected clean parent IDs;
- output record count;
- per-record parent linkage;
- image and annotation hashes;
- validation results; and
- encountered errors and warnings.

Stable ordering must be used before seeded selection so results do not depend on filesystem enumeration order.

## Planned validation gates

All attack families should pass the following checks before use:

- requested and generated counts agree;
- every referenced file exists and is readable;
- output image structure is valid;
- hashes match output bytes and annotation content;
- every derived parent ID exists in the clean manifest;
- no output path points into the clean dataset;
- no holdout record is selected;
- sample IDs and annotation IDs satisfy the attack-specific uniqueness policy;
- category IDs and bounding boxes remain valid unless the explicit test case targets that validation; and
- the intended attack-specific difference is present and limited to the configured scope.

An intentionally invalid field may be retained only when it is the documented subject of the test case. It must be reported as expected invalidity rather than silently normalized.

## Approval gates before implementation

Implementation should not begin until the following are approved:

- output directory and attacked-manifest schema;
- canonical attack type and status values;
- per-family sample counts or rates;
- seeds and parameter ranges;
- label mappings for label-based attacks;
- trigger specification;
- duplicate multiplicity rules;
- OOD definition and source; and
- contributor threat scenarios and synthetic identifier policy.

## Current limitations

- This is a strategy document; no generator behavior has been tested.
- No attack output schema has been finalized.
- No sample counts, rates, severity levels, or parameter values have been approved.
- No OOD source or trigger pattern has been selected.
- No evaluation metrics or detection performance results exist.

