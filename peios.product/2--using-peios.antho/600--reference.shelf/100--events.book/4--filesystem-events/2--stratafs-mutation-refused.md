---
title: STRATAFS_MUTATION_REFUSED
description: Refusals that come from how a mount is arranged rather than from an access check — what counts, two irregularities, and what is not audited at all.
---

Fires when a mutation is refused because of how the mount is arranged,
rather than because of an access check.

Event type string: `STRATAFS_MUTATION_REFUSED`.

| Key | Meaning |
|---|---|
| `path` | The relative path within the mount. |
| `operation` | The operation name. |
| `provider_index` | The provider stratum's index. |
| `provider_stratum` | That stratum's path. |
| `errno` | The refusal. |
| deferred flag | Whether the refusal was deferred. |

## What counts as an arrangement refusal

One explicit list, matching the specification's enumeration exactly:
`EROFS`, `EXDEV`, `ENOTDIR`, `EISDIR`, `ENOTEMPTY`, `EEXIST`, `EINVAL`.

Call sites cover every mutating path — writes, mappings, truncation,
`fallocate`, splice, `copy_file_range`, `remap_file_range`, `setattr`,
`setxattr`, `removexattr`, creation, tmpfile, unlink, rmdir, link,
supersede and rename.

**`EACCES` is deliberately absent.** A refusal produced by an access
check is audited by the mechanism that performed it, and StrataFS does
not duplicate those records. Looking here for a permission denial finds
nothing; look for `access-audit` (§3.1) instead.

## What these records are for

They report a mismatch between what a caller attempted and how the mount
is arranged — software writing where it cannot, or an arrangement that
does not admit an operation someone expected.

That is diagnostic information about configuration, and it is otherwise
visible only as an error returned to a caller that may well discard it.

Rollbacks are audited under this same type with the deferred flag set: a
create or link whose outer bookkeeping failed and whose lower object
could not be removed again, and a failed publication rollback after a
copy-up.

## Two irregularities

**A refusal raised before a provider is known** — creation, tmpfile, the
heads of link and rename — passes a provider index of `-1`, so
`provider_stratum` is emitted as an empty string. The specification asks
for the provider stratum in every refusal record, so this is a gap
rather than a design.

**A refused deferred deletion is audited on any non-zero result**, not
only on the arrangement errors, so one refused by an access check does
produce a StrataFS record. This is a deliberate exception to the
`EACCES` exclusion above: the requirement to audit a deferred deletion
is unconditional, because by then nobody is left to receive the error.

## What is not audited

Resolution, revalidation and enumeration emit nothing. They occur on
every path operation, reveal nothing the resulting access check does
not, and recording them would produce volume out of all proportion to
their significance. There is no audit call anywhere in the lookup path.

Access checks against provider objects are audited by KACS under its own
rules.
