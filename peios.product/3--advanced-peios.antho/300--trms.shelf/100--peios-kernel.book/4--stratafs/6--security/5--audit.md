---
title: Audit
description: The two stratafs events recorded because the information cannot be recovered afterwards — plus two gaps and what is not audited at all.
---

Two classes of stratafs event carry information that cannot be
recovered from the filesystem afterwards, and are recorded when they
happen. Both are emitted through KACS's kernel-only emitter, so KMES
stamps each with the effective token of the task whose operation caused
it. [*audit.events-stamped-with-effective-token]

## Copy-up

Every copy-up emits a record, successful or not. [*audit.copy-up-always-emitted] The payload is a map
of six keys: [*audit.copy-up-payload-keys]

| Key | |
|---|---|
| `path` | The relative path within the mount, `/`-prefixed |
| `provider_index` | The stratum the object was copied from |
| `provider_stratum` | That stratum's path |
| `create_index` | The stratum it was copied into |
| `create_stratum` | That stratum's path |
| `result_errno` | Zero on success, the failure otherwise |

The caller's identity is not in this payload. It does not need to be:
KMES stamps the effective, true and process token GUIDs onto every event
header at ring-write time, and because copy-up runs in the caller's own
context those are the caller's. [*audit.identity-in-event-header] The identity is carried in the
**envelope**, once, for every event — duplicating it into the payload
would give a reader a second copy that could disagree with the first.

Recording it matters because §4.6.3 preserves the source's descriptor,
so nothing about the resulting object records who caused it to exist.
A reader of these records must take the identity from the event header,
not look for it among the keys.

The `ENOTDIR` of parent materialisation is reported through this event
with its `result_errno` rather than through the refusal event below;
the required fields are all present, under a different name. [*audit.parent-materialisation-enotdir-in-copy-up-event]

## Refused mutation

A mutation refused because of how the mount is arranged emits a record
with six keys: the path, the operation name, the provider index, the
provider stratum path, the errno, and whether the refusal was deferred. [*audit.refusal-payload-keys]
The provider stratum is a string where a provider is known and msgpack
nil where none is; see below.

What counts as an arrangement refusal is one explicit list — `EROFS`,
`EXDEV`, `ENOTDIR`, `EISDIR`, `ENOTEMPTY`, `EEXIST`, `EINVAL`. [*audit.refusal-errno-list] Call
sites cover
every mutating path: writes, mappings, truncation, `fallocate`, splice,
`copy_file_range`, `remap_file_range`, `setattr`, `setxattr` and
`removexattr`, creation, tmpfile, unlink and rmdir, link, supersede,
and rename. [*audit.refusal-covers-every-mutating-path]

`EACCES` is deliberately absent from that list. A refusal produced by an
access check is audited by the mechanism that performed it, and
stratafs does not duplicate those records. [*audit.no-record-for-access-refusal]

These refusals report a mismatch between what a caller attempted and
how the mount is arranged — software writing where it cannot, or an
arrangement that does not admit an operation someone expected. That is
diagnostic information about the system's configuration, and it is
otherwise visible only as an error returned to a caller that may
discard it.

Rollbacks are audited under the same event with the deferred flag set:
a create or link whose outer bookkeeping failed and whose lower object
could not be removed again, and a failed publication rollback after a
copy-up. [*audit.rollback-uses-deferred-flag]

A refusal raised before a provider is known — creation, tmpfile, the
heads of link and rename — has no stratum to name. It reports a provider
index of `-1` and a `provider_stratum` of msgpack **nil**, so a reader
can tell "no provider was involved" from "the provider's path is empty".
The two fields agree: an index of `-1` always accompanies a nil stratum. [*audit.unknown-provider-index-and-nil-stratum]

### One exception

A refused **deferred deletion** is audited on *any* non-zero result, not
only the arrangement errors, so one refused by an access check does get
a stratafs record. [*audit.deferred-deletion-audited-on-any-error] That is the right resolution of the two rules, since
the requirement to audit a deferred deletion is unconditional — nobody
is left to receive the error — but it is a deliberate exception to the
`EACCES` exclusion above.

## What is not audited

Resolution, revalidation and enumeration emit no records of their own.
They occur on every path operation, they reveal nothing the resulting
access check does not, and recording them would produce volume out of
all proportion to their significance. There is no audit call anywhere
in the lookup path. [*audit.lookup-not-audited]

Access checks performed against provider objects are audited by KACS,
under its own rules.
