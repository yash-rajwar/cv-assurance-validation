# Duplicate Attack Generator

Status: **framework placeholder only**. No attack generator or attacked data exists in this directory.

## Planned purpose

This attack family will simulate duplicated submissions or records by creating explicitly identified copies of selected development samples. Duplicate records will receive unique sample IDs while retaining a reference to the clean parent.

## Planned controls

- Select parent samples deterministically with a fixed seed.
- Copy files rather than modifying or moving clean inputs.
- Preserve byte identity when exact duplication is intended.
- Assign unique attacked sample IDs and non-null parent IDs.
- Record duplicate multiplicity and configuration.
- Verify file hashes, record uniqueness, expected duplicate groups, and split isolation.

See `documentation/ATTACK_PLAN.md` for the common future-generation protocol.

