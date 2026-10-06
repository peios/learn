---
title: Audit
description: The two stratafs events recorded because the information cannot be recovered afterwards — plus two gaps and what is not audited at all.
---

Two classes of stratafs event carry information that cannot be
recovered from the filesystem afterwards, and are recorded when they
happen. Both are emitted through KACS's kernel-only emitter, so KMES
stamps each with the effective token of the task whose operation caused
it. [*audit.events-stamped-with-effective-token]

## Copy-up [*audit.copy-up-always-emitted]

Every copy-up emits a `stratafs.file.copied-up` record, successful or
not. Its payload carries these fields, each a path of nested maps:

| Field | |
|---|---|
| `object.file.path-relative` | The relative path within the mount, `/`-prefixed |
| `source.stratum.index` | The stratum the object was copied from |
| `source.stratum.path` | That stratum's path |
| `destination.stratum.index` | The stratum it was copied into |
| `destination.stratum.path` | That stratum's path |
| `outcome.success` | Whether the copy-up succeeded |
| `outcome.errno` | The failure, as a negative errno; absent on success |

The caller's identity is not in this payload. It does not need to be:
KMES stamps the effective, true and process token GUIDs onto every event
header at ring-write time, and because copy-up runs in the caller's own
context those are the caller's. The identity is carried in the
**envelope**, once, for every event — duplicating it into the payload
would give a reader a second copy that could disagree with the first.

Recording it matters because §4.6.3 preserves the source's descriptor,
so nothing about the resulting object records who caused it to exist.
A reader of these records must take the identity from the event header,
not look for it among the fields.

The `ENOTDIR` of parent materialisation is reported through this event
in its `outcome.errno` rather than through the refusal event below;
the required fields are all present, under a different event type.

## Refused mutation [*audit.arrangement-refusal-emitted]

A mutation refused because of how the mount is arranged emits a
`stratafs.mutation.refused` record carrying the relative path
(`object.file.path-relative`), the operation (`operation.name`), the
providing stratum (`source.stratum.index` and `source.stratum.path`),
the error (`outcome.errno`, negative) and whether the refusal was
deferred (`outcome.deferred`). The `source.stratum` fields are present
only where a provider is known; see below.

What counts as an arrangement refusal is one explicit list — `EROFS`,
`EXDEV`, `ENOTDIR`, `EISDIR`, `ENOTEMPTY`, `EEXIST`, `EINVAL`. Call
sites cover
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

A refusal raised before a provider is known — creation, tmpfile, the
heads of link and rename — has no stratum to name. Its record has no
`source` map at all: `source.stratum.index` and `source.stratum.path`
are both absent, never `-1`, nil or an empty string, so a reader can
tell "no provider was involved" from "the provider's path is empty".

### One exception [*audit.deferred-deletion-audited-on-any-error]

A refused **deferred deletion** is audited on *any* non-zero result, not
only the arrangement errors, so one refused by an access check does get
a stratafs record. That is the right resolution of the two rules, since
the requirement to audit a deferred deletion is unconditional — nobody
is left to receive the error — but it is a deliberate exception to the
`EACCES` exclusion above.

The record is stratafs's whether or not stratafs was entered. The
delete-child check on the merged parent runs before `->unlink`, so a
directory whose descriptor tightened between the arm and the close
refuses the deletion before the filesystem sees it; KACS then raises
the stratafs record itself, with no `source.stratum` fields, since no
stratum was consulted.

## What is not audited [*audit.lookup-not-audited]

Resolution, revalidation and enumeration emit no records of their own.
They occur on every path operation, they reveal nothing the resulting
access check does not, and recording them would produce volume out of
all proportion to their significance. There is no audit call anywhere
in the lookup path.

Access checks performed against provider objects are audited by KACS,
under its own rules.
