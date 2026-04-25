---
title: Lifecycle States
---

Each version of a PSD MUST have a lifecycle status recorded in its version-level `trail.toml`.

## States

| State | Meaning |
|---|---|
| `draft` | Under active development. Not normative. Content MAY change without notice. |
| `final` | Normative. Implementations MUST conform to this version. |
| `withdrawn` | Retracted. This version was published but later found to be incorrect. |

## Transitions

Lifecycle transitions are one-directional:

- `draft` → `final`: The version has been reviewed and is ready for implementation.
- `draft` → `withdrawn`: The draft was abandoned before finalisation.
- `final` → `withdrawn`: The finalised version was found to contain errors serious enough to retract it. A replacement version SHOULD be published.

A `final` version MUST NOT return to `draft`. If a finalised specification needs semantic changes, a new version MUST be published.

## Errata

Typographical errors in a `final` version MAY be corrected in place without publishing a new version, provided the correction does not change the semantic meaning of any normative statement. If a typo could be read as a different normative requirement, it MUST be treated as a semantic change and corrected via a new version.

A `withdrawn` version MUST NOT transition to any other state. Its PSD number and version directory are retained for historical reference.

## Version succession

Within a specification, a newer `final` version implicitly supersedes all older versions. The version resolution rule (§3.3) determines which version applies in any given context. No explicit `supersedes` metadata is required.

Multiple versions of a specification MAY be `final` simultaneously. This is expected -- a v0.20 and a v0.22 may both be `final`, with the version resolution rule selecting the appropriate one for each referencing context.

## Metadata

The version-level `trail.toml` MUST contain:

```toml
status = "final"
date = "2026-04-20"
```

- `status`: One of `draft`, `final`, or `withdrawn`.
- `date`: The date of the most recent change to this version, in `YYYY-MM-DD` format.
