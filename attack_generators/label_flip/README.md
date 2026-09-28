# Label Flip Attack Generator

Status: **framework placeholder only**. No attack generator or attacked data exists in this directory.

## Planned purpose

This attack family will simulate isolated object-label corruption by replacing selected COCO category IDs with different valid category IDs in copied annotation records. Clean annotations and clean images will remain unchanged.

## Planned controls

- Operate only on explicitly eligible development samples.
- Use a recorded fixed random seed.
- Select target annotations and replacement categories deterministically.
- Never replace a category with itself or introduce an unknown category ID.
- Preserve a link to the clean parent sample.
- Recompute the attacked annotation hash and record the attack parameters.
- Validate annotation counts, category IDs, boxes, provenance, and hashes after generation.

See `documentation/ATTACK_PLAN.md` for the common future-generation protocol.

