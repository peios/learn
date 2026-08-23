---
title: Audit
description: The two stratafs events recorded because the information cannot be recovered afterwards — plus two gaps and what is not audited at all.
---

Two classes of stratafs event carry information that cannot be
recovered from the filesystem afterwards, and are recorded when they
happen. Both are emitted through KACS's kernel-only emitter, so KMES
stamps each with the effective token of the task whose operation caused
it.

## Copy-up

Every copy-up emits a record, successful or not. The payload is a map
of six keys:

| Key | |
|---|---|
| `path` | The relative path within the mount, `/`-prefixed |
| `provider_index` | The stratum the object was copied from |
| `provider_stratum` | That stratum's path |
| `create_index` | The stratum it was copied into |
| `create_stratum` | That stratum's path |
| `result_errno` | Zero on success, the failure otherwise |

The caller's identity is required because §4.6.3 preserves the source's
descriptor, so nothing about the resulting object records who caused it
to exist. It is present — but as an **envelope** field rather than a
payload one. KMES stamps the effective, true and process token GUIDs
onto the event header at ring-write time, and because copy-up runs in
the caller's own context those are the caller's. Nothing in the payload
names a token.

The `ENOTDIR` of parent materialisation is reported through this event
with its `result_errno` rather than through the refusal event below;
the required fields are all present, under a different name.

## Refused mutation

A mutation refused because of how the mount is arranged emits a record
with six keys: the path, the operation name, the provider index, the
provider stratum path, the errno, and whether the refusal was deferred.

What counts as an arrangement refusal is one explicit list — `EROFS`,
`EXDEV`, `ENOTDIR`, `EISDIR`, `ENOTEMPTY`, `EEXIST`, `EINVAL` — which
matches the specification's enumeration one for one. Call sites cover
every mutating path: writes, mappings, truncation, `fallocate`, splice,
`copy_file_range`, `remap_file_range`, `setattr`, `setxattr` and
`removexattr`, creation, tmpfile, unlink and rmdir, link, supersede,
and rename.

`EACCES` is deliberately absent from that list. A refusal produced by an
access check is audited by the mechanism that performed it, and
stratafs does not duplicate those records.

These refusals report a mismatch between what a caller attempted and
how the mount is arranged — software writing where it cannot, or an
arrangement that does not admit an operation someone expected. That is
diagnostic information about the system's configuration, and it is
otherwise visible only as an error returned to a caller that may
discard it.

Rollbacks are audited under the same event with the deferred flag set:
a create or link whose outer bookkeeping failed and whose lower object
could not be removed again, and a failed publication rollback after a
copy-up.

### Two gaps

A refusal raised before a provider is known — creation, tmpfile, the
heads of link and rename — passes a provider index of `-1`, so the
provider stratum is emitted as an empty string. The specification asks
for the provider stratum in every refusal record.

A refused **deferred deletion** is audited on *any* non-zero result, not
only the arrangement errors, so one refused by an access check does get
a stratafs record. That is the right resolution of the two rules, since
the requirement to audit a deferred deletion is unconditional — nobody
is left to receive the error — but it is a deliberate exception to the
`EACCES` exclusion above.

## What is not audited

Resolution, revalidation and enumeration emit no records of their own.
They occur on every path operation, they reveal nothing the resulting
access check does not, and recording them would produce volume out of
all proportion to their significance. There is no audit call anywhere
in the lookup path.

Access checks performed against provider objects are audited by KACS,
under its own rules.
