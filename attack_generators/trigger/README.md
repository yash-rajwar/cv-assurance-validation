# Trigger Attack Generator

Status: **framework placeholder only**. No trigger pattern, generator, or attacked image exists in this directory.

## Planned purpose

This attack family will simulate controlled visual-trigger contamination by applying a fully specified pattern to copies of eligible development images.

## Planned controls

- Specify and version trigger content, position, dimensions, opacity, and compositing rule.
- Use a fixed seed for randomized placement or sample selection.
- Never alter clean source images in place.
- Preserve parent linkage and record all transformation parameters.
- Recompute image hashes after transformation.
- Validate image readability, dimensions, expected pixel changes, provenance, and hashes.

See `documentation/ATTACK_PLAN.md` for the common future-generation protocol.

