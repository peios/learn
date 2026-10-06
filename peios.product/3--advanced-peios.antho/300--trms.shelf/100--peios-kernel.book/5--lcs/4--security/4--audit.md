---
title: Audit
description: The seven audit events LCS emits, which are unconditional, and what happens when emission itself fails.
---

LCS emits audit events through KMES. Seven events exist. [*lcs-audit.seven-events-through-kmes]

| Event | Emitted when |
|---|---|
| `lcs.audit.key.opened` | A key open matched a SACL audit ACE. [*lcs-audit.key-open.on-sacl-match] |
| `lcs.audit.backup.started` | Before `REG_IOC_BACKUP` reads any subtree data. [*lcs-audit.backup-start.before-any-read] |
| `lcs.audit.backup.ended` | After a backup completes or fails after starting. [*lcs-audit.backup-complete.after-finish-or-failure] |
| `lcs.audit.restore.started` | Before `REG_IOC_RESTORE` modifies any source state. [*lcs-audit.restore-start.before-any-mutation] |
| `lcs.audit.restore.ended` | After a restore completes or fails after starting. [*lcs-audit.restore-complete.after-finish-or-failure] |
| `lcs.source.response.rejected` | LCS rejected malformed source data. [*lcs-audit.validation-failure.on-malformed-source-data] |
| `lcs.config.value.rejected` | LCS rejected an invalid self-configuration value. [*lcs-audit.self-config-invalid.on-invalid-value] |

Backup and restore are audited **unconditionally**, whatever the SACL
on the target key says. [*lcs-audit.backup-and-restore-unconditional] They are privilege-gated bulk operations that
bypass per-key access checks entirely, so the audit trail is the only
record that they happened.

Every payload is a single MessagePack map with string keys. [*lcs-audit.payload-is-a-msgpack-map]
Each field path is written as nested maps, one per segment, so
`object.key.guid` is `{object: {key: {guid: …}}}`. A value LCS does not
have is left out rather than written as nil, and every map counts only
the keys actually written (PGSS §6.4).

The key GUID, `object.key.guid`, is a 16-byte binary value, and the
caller's SID is a binary KACS encoding. The token and process GUIDs
are not payload fields at all: they ride in the KMES event header, so
the payload never repeats them. [*lcs-audit.payload-guid-and-sid-encoding]

## The caller summary

Five of the seven describe the effective token used for the operation
under `subject.token`. It has six fields and no more: `sid`,
`integrity`, `id` (the token's LUID), `auth-id` (its logon session's
LUID), `type` (`primary` or `impersonation`) and `impersonation`, the
impersonation level. [*lcs-audit.caller-summary-nine-fields]

The bound is deliberate. Group lists, privilege arrays, claims and
default DACLs are unbounded and are never included. The summary carries
enough to correlate an event with a caller, and nothing that could make
one event arbitrarily large. `lcs.source.response.rejected` and
`lcs.config.value.rejected` carry no caller: neither is a principal
acting.

A primary token reports an impersonation
level of 0. [*lcs-audit.primary-token-impersonation-level-zero] An Anonymous impersonation token also
reports 0, which is why `subject.token.type` is recorded beside it.

## Key opens

`lcs.audit.key.opened` carries the caller summary, then
`object.kind` (always `key`, which names the table the masks decode
against), `object.key.guid`, the requested and granted masks as
`access.requested` and `access.granted`, `outcome.success` (`true`
when the open was allowed), and `trigger.sacl-match` — bit 0 for a
success-audit match, bit 1 for a failure-audit match, no other
bits. [*lcs-audit.key-open.payload-fields]

`access.granted` is forced to zero on a denial, and that is enforced
rather than merely intended: a denied event carrying a non-zero granted
mask is rejected as a malformed payload. [*lcs-audit.key-open.denied-event-has-zero-granted]

`access.requested` is the mask
after registry generic mapping, with `MAXIMUM_ALLOWED` re-added if the
caller asked for it. [*lcs-audit.key-open.requested-access-is-post-mapping]

SACL evaluation follows the KACS AccessCheck algorithm — the SACL is
evaluated alongside the DACL, not separately. [*lcs-audit.sacl-evaluated-with-the-dacl]

Reading or modifying a
SACL requires `ACCESS_SYSTEM_SECURITY`, which is itself gated by
`SeSecurityPrivilege`. [*lcs-audit.sacl-access-gated-by-sesecurityprivilege]

A request of `MAXIMUM_ALLOWED` **alone** maps to a desired mask of zero,
so AccessCheck's SACL walk matches each audit ACE against the *granted*
mask instead. [*lcs-audit.key-open.maximum-allowed-matches-granted-mask] An audit ACE says "audit when someone gets this right",
and with `MAXIMUM_ALLOWED` they did get it.

Such an open therefore
always audits as a success, which is correct: `MAXIMUM_ALLOWED` returns
whatever is available and never fails, so a failure ACE has nothing to
record. [*lcs-audit.key-open.maximum-allowed-always-audits-success]

An ACE naming a right the caller did not receive still does not
match. [*lcs-audit.key-open.ace-for-ungranted-right-does-not-match]

## Backup and restore

`lcs.audit.backup.started` and `lcs.audit.restore.started` carry the
caller summary, `object.key.guid` for the subtree root, and
`operation.fd`, the descriptor the stream is written to or read from.

`lcs.audit.backup.ended` and `lcs.audit.restore.ended` carry the
caller summary, `object.key.guid` and `outcome.success`. When the
operation failed they also carry `outcome.errno`, the error as a
negative errno; on success it is absent.

## Source validation failures

`lcs.source.response.rejected` carries the source slot as
`source.rsi.slot` and then, where each is known, the hive name as
`source.rsi.hive`, the RSI request id and operation code as
`request.id` and `request.op-code`, and the key GUID as
`object.key.guid`. [*lcs-audit.validation-failure.payload-fields] `outcome.reason` names what was wrong.
There are twelve:

`malformed-security-descriptor`, `malformed-layer-name`,
`unknown-rsi-status-code`, `future-sequence-number`,
`duplicate-winning-sequence-tie`,
`malformed-layer-metadata-security-descriptor`,
`malformed-key-name`, `malformed-value-name`,
`malformed-response-payload`, `malformed-key-metadata`,
`malformed-value-payload`, `malformed-delete-layer-orphan-list`. [*lcs-audit.validation-failure.twelve-classes]

The three name classes are field-specific: layer-name fields, key
component or child-name fields, and value-name fields respectively. [*lcs-audit.validation-failure.name-classes]

The structural classes cover a response whose operation-specific
payload has the wrong shape or trailing bytes; a lookup or
enumeration whose metadata block is incomplete, duplicated,
unreferenced or nil; a value payload with an invalid type, a
tombstone/data mismatch or oversized data; and an invalid orphan GUID
array from `RSI_DELETE_LAYER`. [*lcs-audit.validation-failure.structural-classes]

## Configuration

`lcs.config.value.rejected` has the same shape as KMES's
`kmes.config.value.rejected`, with every field under one `config`
map. It carries the offending parameter's key and name as
`config.key.path` and `config.name`; the expected type and numeric
range as `config.expected.type`, `config.expected.min` and
`config.expected.max`; what was actually received as
`config.received.kind` — one of `missing`, `wrong-type` or
`out-of-range` — with `config.received.type` for a value of the wrong
type or `config.received.value` for one out of range; and, as
`config.value`, the value LCS retained instead. [*lcs-audit.self-config.payload-fields]

Because `missing` counts as invalid, a first boot before seed restore
emits one of these per parameter on each refresh: nineteen events
against an empty `Registry\` key. [*lcs-audit.self-config.missing-counts-as-invalid] That is correct and expected, but it
is a noticeable share of the boot audit stream.

## What happens when emission fails

The policy differs per event, and the differences are the point.

- **`lcs.audit.key.opened`.** If LCS cannot *construct* a valid payload —
  corrupt internal state, allocation failure, anything on the LCS side
  — the open fails with `EIO` and no key fd is published. [*lcs-audit.emit-failure.key-open-construct-failure-fails-the-open] If the
  payload is valid but KMES cannot *retain* the event — unavailable,
  ring drops, capacity pressure, no consumer — the access decision and
  the fd publication are unaffected. Loss accounting is KMES's problem. [*lcs-audit.emit-failure.key-open-retain-failure-is-harmless]
- **`lcs.audit.backup.started`, `lcs.audit.restore.started`.** Emission
  failure returns `EIO` and the operation does not start. Nothing is
  read and nothing is written. [*lcs-audit.emit-failure.start-events-block-the-operation]
- **`lcs.audit.backup.ended`, `lcs.audit.restore.ended`.** The operation
  has already finished. Emission is attempted; failure does not change
  the result. [*lcs-audit.emit-failure.complete-events-are-best-effort]
- **`lcs.source.response.rejected`.** The triggering operation is
  already failing with `EIO`. Emission is attempted; failure does not
  change that. [*lcs-audit.emit-failure.validation-failure-is-best-effort]
- **`lcs.config.value.rejected`.** The invalid value has already been
  ignored and the previous known-good value retained. Emission is
  attempted; failure leaves the retained configuration in force. [*lcs-audit.emit-failure.self-config-is-best-effort]

The rule underneath all five: an audit failure blocks an operation only
where the audit record is the *point* of the operation being permitted.
A privileged bulk export whose start could not be recorded does not
happen. A key open whose decision could not be recorded does not
happen. Everything downstream of an already-determined outcome records
what it can.

LCS constructs the payload and attempts to enqueue it before
continuing past the audit point. It never waits for a userspace
consumer to observe or retain the event. [*lcs-audit.enqueue-without-awaiting-a-consumer]
