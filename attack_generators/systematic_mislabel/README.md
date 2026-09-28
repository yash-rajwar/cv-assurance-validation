# Systematic Mislabel Attack Generator

Status: **framework placeholder only**. No attack generator or attacked data exists in this directory.

## Planned purpose

This attack family will simulate consistent, rule-driven category corruption. A recorded mapping, such as one valid COCO category to another, will be applied to copied annotations across a deterministic development subset.

## Planned controls

- Define and version the category mapping before generation.
- Reject identity mappings, unknown category IDs, and ambiguous rules.
- Use a fixed seed when sample selection is randomized.
- Apply the same mapping consistently within one attack configuration.
- Preserve clean parent linkage and leave source annotations unchanged.
- Recompute annotation hashes and validate the complete output.

See `documentation/ATTACK_PLAN.md` for the common future-generation protocol.

