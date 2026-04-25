---
title: PSD Numbers
---

Every Peios specification MUST be assigned a PSD number. The PSD number is the primary citation handle for the specification and is permanent for the life of the specification.

## Assignment

PSD numbers MUST be assigned per specification, not per version. A specification that has versions v0.20, v0.22, and v0.56.1 has one PSD number, not three.

PSD numbers MUST be sequential positive integers assigned in order of specification creation. The first specification is PSD-001, the second is PSD-002, and so on.

PSD numbers MUST be assigned when the specification is created. A specification is citable by PSD number while still in draft status.

PSD numbers MUST NOT be reused. A withdrawn specification retains its PSD number.

## Format

In prose, PSD numbers MUST be written as `PSD-` followed by the number zero-padded to three digits: PSD-001, PSD-012, PSD-103.

> [!INFORMATIVE]
> Three-digit padding accommodates up to 999 specifications. If the corpus exceeds this, the padding width increases but existing citations remain valid -- PSD-001 is the same specification whether the corpus has 5 or 5000 entries.

## Directory naming

The PSD number MUST be encoded in the specification's directory name using the format `psd-NNN--name`, where:

- `NNN` is the PSD number zero-padded to three digits
- `--` is a literal double hyphen separator
- `name` is a short kebab-case identifier for the specification

The `--` separator MUST be used to separate the PSD number from the name. This makes the two components machine-parseable (split on `--`) and visually distinct from hyphenated names.

The short name MUST be lowercase. It MUST use only ASCII lowercase letters, digits, and hyphens. It SHOULD be short (one to two words). It MUST NOT start or end with a hyphen. Multi-word names MUST use hyphens as separators (kebab-case).

Examples:

```
specs/psd-001--psd/
specs/psd-002--binary-identifiers/
specs/psd-003--kmes/
specs/psd-004--kacs/
specs/psd-005--eventd/
specs/psd-006--lcs/
specs/psd-007--loregd/
specs/psd-008--peinit/
```

> [!INFORMATIVE]
> Related specifications naturally cluster in directory listings because they are assigned PSD numbers around the same time. The directory naming scheme serves both as an identifier and as a sort key.
