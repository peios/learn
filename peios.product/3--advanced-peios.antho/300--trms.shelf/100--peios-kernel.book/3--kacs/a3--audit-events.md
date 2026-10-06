---
title: Audit Event Schemas
description: The audit records KACS emits through KMES — the event families, their shared payload records, and how they are delivered.
---

KACS emits its audit records through KMES with origin class 2 (§2.2). [*audit-events.origin-class-two]
Each event's payload is a msgpack map whose field paths follow PGSS
§6.4: `access.requested` is the key `requested` inside the map under
`access`, never a key containing a dot, and a value the emitter does
not have is absent rather than nil. The shared `subject` group — the
effective token's `subject.token.*`, the PIP state in `subject.pip.*`,
and the calling process as `emitter.process.{pid,name,executable}` — is
attached at emission time from the resolved call context rather than by
the evaluation pipeline (§3.8.9).

This appendix covers which events KACS emits and from where. The
field-by-field payload schemas are in the
[Peios Events Index](~peios/events/all-event-types), which is
canonical for them, and `evman <event-type>` prints each one.

## Event families

| Event type | Emitted by |
|---|---|
| `kacs.audit.access.checked` | The SACL walk, and token audit-policy forcing. [*audit-events.access-audit-record] |
| `kacs.audit.handle.used` | Enforcement points, per operation, against a handle's continuous audit mask. [*audit-events.continuous-audit-record] |
| `kacs.audit.privilege.used` | Privilege-use auditing, for the five AccessCheck-influencing privileges. [*audit-events.privilege-use-record] |
| `kacs.caap.sacl.skipped`, `kacs.caap.staging.diverged` | A CAAP rule SACL that could not be parsed or evaluated; a staged result that differs from the effective one. [*audit-events.caap-policy-diagnostic-record] |
| `kacs.session.destroyed` | LogonSession teardown (§3.2.7). [*audit-events.logon-session-destroyed-record] |
| `kacs.descriptor.rejected` | A descriptor xattr that exists but fails structural validation (§3.9.5). [*audit-events.corrupt-sd-record] |
| `stratafs.file.copied-up` | StrataFS copy-up lifecycle and failure (§3.9.7). [*audit-events.stratafs-copy-up-record] |
| `stratafs.mutation.refused` | A StrataFS arrangement refusal. [*audit-events.stratafs-mutation-refused-record] |

`kacs.descriptor.rejected` carries `object.kind` `file` and
`outcome.reason` `corrupt`. It does not name the file: the descriptor is
read through internal path anchors whose mount cannot always be resolved
to an absolute path, so `object.file.path` is absent.

KACS also writes `kacs.signature.crypto.failed` once at boot when the
signature transform is unavailable (§3.6), carrying
`signature.crypto-stage` `boot-probe` and the negative `outcome.errno`.

The `privilege.name` field of a `kacs.audit.privilege.used` event carries a canonical
name, and only five are representable — `SeSecurityPrivilege`,
`SeTakeOwnershipPrivilege`, `SeBackupPrivilege`, `SeRestorePrivilege`
and `SeRelabelPrivilege`. [*audit-events.privilege-five-canonical-names] Any other bit fails the encoder closed
rather than emitting an unnamed privilege, which is consistent with
those being the only five that can produce such an event at all
(§3.4.1). [*audit-events.privilege-encoder-fails-closed]

`kacs.audit.handle.used` carries an `operation.name` naming the enforcement
point: `file.access`, `file.mmap`, `file.mprotect`, `file.permission`,
`file.write`, `file.ioctl`, `file.lock`, `file.fcntl`, `file.truncate`
and `file.fallocate`. [*audit-events.continuous-operation-names] It never carries a caller-supplied audit context: its
`object.kind` is always `file`, with the handle's absolute path in
`object.file.path` (absent only if the path cannot be resolved), and it
never sets `fields.attestation.userspace`. [*audit-events.continuous-object-context-nil]

## Delivery

Audit and privilege-use events are delivered **before** any result is
written back to the caller, and a delivery failure fails the syscall
with `EIO` or `EOPNOTSUPP`. [*audit-events.delivered-before-result] An audit event cannot be suppressed by
handing the call a bad output pointer.

Three emissions are best-effort by contrast, and drop silently rather
than failing the operation that caused them:

- `kacs.session.destroyed` where the authentication package name is
  not valid UTF-8. [*audit-events.best-effort-logon-session-utf8]
- The two StrataFS events on an allocation failure or an over-long
  operation string. [*audit-events.best-effort-stratafs]
- Any self-emitted payload that would exceed its encoding buffer. [*audit-events.best-effort-oversize-payload]

The transport itself — ring buffer delivery, buffering and drop
accounting — is KMES's (§2.5, §2.7).
