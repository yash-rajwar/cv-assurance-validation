# Out-of-Distribution Attack Generator

Status: **framework placeholder only**. No generator, external source, or out-of-distribution data has been selected.

## Planned purpose

This attack family will evaluate handling of samples outside the intended COCO-derived distribution. The exact out-of-distribution definition and source must be approved before acquisition or generation.

## Planned controls

- Define the out-of-distribution criterion before selecting samples.
- Record source, version, acquisition date, provenance, and permitted use.
- Keep external samples separate from the clean COCO dataset.
- Assign new sample IDs; do not imply a COCO parent when none exists.
- Record any preprocessing and compute hashes after finalization.
- Validate file integrity, metadata, provenance, and manifest completeness.

See `documentation/ATTACK_PLAN.md` for the common future-generation protocol.

