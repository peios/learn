---
title: Audit Event Schemas
description: The audit records KACS emits through KMES — the event families, their shared payload records, and how they are delivered.
---

KACS emits its audit records through KMES with origin class 2 (§2.2).
Each event's payload is a msgpack map; the shared `subject` and
`process` sub-maps are attached at emission time from the resolved
call context rather than by the evaluation pipeline (§3.8.9).

This appendix covers which events KACS emits and from where. The
field-by-field payload schemas are in the
[Peios Events Index](~peios/kernel-access-events/access-audit), which is
canonical for them.

## Event families

| Event type | Emitted by |
|---|---|
| `access-audit` | The SACL walk, and token audit-policy forcing. |
| `continuous-audit` | Enforcement points, per operation, against a handle's continuous audit mask. |
| `privilege-use` | Privilege-use auditing, for the five AccessCheck-influencing privileges. |
| `caap-policy-diagnostic` | A CAAP rule SACL error, or a staged-versus-effective mismatch. |
| `logon-session-destroyed` | LogonSession teardown (§3.2.7). |
| `corrupt-sd` | A descriptor xattr that exists but fails structural validation (§3.9.5). |
| `STRATAFS_COPY_UP` | StrataFS copy-up lifecycle and failure (§3.9.7). |
| `STRATAFS_MUTATION_REFUSED` | A StrataFS arrangement refusal. |

The `privilege` field of a `privilege-use` event carries a canonical
name, and only five are representable — `SeSecurityPrivilege`,
`SeTakeOwnershipPrivilege`, `SeBackupPrivilege`, `SeRestorePrivilege`
and `SeRelabelPrivilege`. Any other bit fails the encoder closed
rather than emitting an unnamed privilege, which is consistent with
those being the only five that can produce such an event at all
(§3.4.1).

`continuous-audit` carries an `operation` naming the enforcement
point: `file.access`, `file.mmap`, `file.mprotect`, `file.permission`,
`file.write`, `file.ioctl`, `file.lock`, `file.fcntl`, `file.truncate`
and `file.fallocate`. Its `object_context` field is always nil.

## Delivery

Audit and privilege-use events are delivered **before** any result is
written back to the caller, and a delivery failure fails the syscall
with `EIO` or `EOPNOTSUPP`. An audit event cannot be suppressed by
handing the call a bad output pointer.

Three emissions are best-effort by contrast, and drop silently rather
than failing the operation that caused them:
`logon-session-destroyed` where the authentication package name is not
valid UTF-8; the two StrataFS events on an allocation failure or an
over-long operation string; and any self-emitted payload that would
exceed its encoding buffer.

The transport itself — ring buffer delivery, buffering and drop
accounting — is KMES's (§2.5, §2.7).
