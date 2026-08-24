---
title: Audit
description: The seven audit events LCS emits, which are unconditional, and what happens when emission itself fails.
---

LCS emits audit events through KMES. Seven events exist.

| Event | Emitted when |
|---|---|
| `LCS_KEY_OPEN_AUDIT` | A key open matched a SACL audit ACE. |
| `LCS_BACKUP_START` | Before `REG_IOC_BACKUP` reads any subtree data. |
| `LCS_BACKUP_COMPLETE` | After a backup completes or fails after starting. |
| `LCS_RESTORE_START` | Before `REG_IOC_RESTORE` modifies any source state. |
| `LCS_RESTORE_COMPLETE` | After a restore completes or fails after starting. |
| `LCS_SOURCE_VALIDATION_FAILURE` | LCS rejected malformed source data. |
| `LCS_SELF_CONFIG_INVALID` | LCS rejected an invalid self-configuration value. |

Backup and restore are audited **unconditionally**, whatever the SACL
on the target key says. They are privilege-gated bulk operations that
bypass per-key access checks entirely, so the audit trail is the only
record that they happened.

Every payload is a single MessagePack map with string keys. GUIDs are
16-byte binary values; SIDs are binary KACS encodings.

## The caller summary

Six of the seven carry a `caller` submap describing the effective
token used for the operation. It has nine fields and no more:
`effective_token_guid`, `true_token_guid`, `process_guid` and
`user_sid`, then `authentication_id`, `token_id`, `token_type`,
`impersonation_level` and `integrity_level`.

The bound is deliberate. Group lists, privilege arrays, claims and
default DACLs are unbounded and are never included. The summary carries
enough to correlate an event with a caller, and nothing that could make
one event arbitrarily large. A primary token reports an impersonation
level of 0.

## Key opens

`LCS_KEY_OPEN_AUDIT` carries the caller summary, the key GUID, the
requested and granted access masks, the decision (`allowed` or
`denied`) and `sacl_match_flags` — bit 0 for a success-audit match, bit
1 for a failure-audit match, no other bits.

`granted_access` is forced to zero on a denial, and that is enforced
rather than merely intended: a denied event carrying a non-zero granted
mask is rejected as a malformed payload. `requested_access` is the mask
after registry generic mapping, with `MAXIMUM_ALLOWED` re-added if the
caller asked for it.

SACL evaluation follows the KACS AccessCheck algorithm — the SACL is
evaluated alongside the DACL, not separately. Reading or modifying a
SACL requires `ACCESS_SYSTEM_SECURITY`, which is itself gated by
`SeSecurityPrivilege`.

A request of `MAXIMUM_ALLOWED` **alone** maps to a desired mask of zero,
so AccessCheck's SACL walk matches each audit ACE against the *granted*
mask instead. An audit ACE says "audit when someone gets this right",
and with `MAXIMUM_ALLOWED` they did get it. Such an open therefore
always audits as a success, which is correct: `MAXIMUM_ALLOWED` returns
whatever is available and never fails, so a failure ACE has nothing to
record. An ACE naming a right the caller did not receive still does not
match.

## Source validation failures

`LCS_SOURCE_VALIDATION_FAILURE` carries the source slot identifier and
then, where each is known, the hive name, the RSI request id, the
operation code and the key GUID. The last field, `validation_class`,
names what was wrong. There are twelve:

`malformed_security_descriptor`, `malformed_layer_name`,
`unknown_rsi_status_code`, `future_sequence_number`,
`duplicate_winning_sequence_tie`,
`malformed_layer_metadata_security_descriptor`,
`malformed_key_name`, `malformed_value_name`,
`malformed_response_payload`, `malformed_key_metadata`,
`malformed_value_payload`, `malformed_delete_layer_orphan_list`.

The three name classes are field-specific: layer-name fields, key
component or child-name fields, and value-name fields respectively.
The structural classes cover a response whose operation-specific
payload has the wrong shape or trailing bytes; a lookup or
enumeration whose metadata block is incomplete, duplicated,
unreferenced or nil; a value payload with an invalid type, a
tombstone/data mismatch or oversized data; and an invalid orphan GUID
array from `RSI_DELETE_LAYER`.

## Configuration

`LCS_SELF_CONFIG_INVALID` carries the parent path and value name of
the offending parameter, the expected type and numeric range, what was
actually received — one of `missing`, `wrong_type` or
`dword_out_of_range`, with the actual type or value where applicable —
and the value LCS retained instead.

Because `missing` counts as invalid, a first boot before seed restore
emits one of these per parameter on each refresh: nineteen events
against an empty `Registry\` key. That is correct and expected, but it
is a noticeable share of the boot audit stream.

## What happens when emission fails

The policy differs per event, and the differences are the point.

- **`LCS_KEY_OPEN_AUDIT`.** If LCS cannot *construct* a valid payload —
  corrupt internal state, allocation failure, anything on the LCS side
  — the open fails with `EIO` and no key fd is published. If the
  payload is valid but KMES cannot *retain* the event — unavailable,
  ring drops, capacity pressure, no consumer — the access decision and
  the fd publication are unaffected. Loss accounting is KMES's problem.
- **`LCS_BACKUP_START`, `LCS_RESTORE_START`.** Emission failure returns
  `EIO` and the operation does not start. Nothing is read and nothing
  is written.
- **`LCS_BACKUP_COMPLETE`, `LCS_RESTORE_COMPLETE`.** The operation has
  already finished. Emission is attempted; failure does not change the
  result.
- **`LCS_SOURCE_VALIDATION_FAILURE`.** The triggering operation is
  already failing with `EIO`. Emission is attempted; failure does not
  change that.
- **`LCS_SELF_CONFIG_INVALID`.** The invalid value has already been
  ignored and the previous known-good value retained. Emission is
  attempted; failure leaves the retained configuration in force.

The rule underneath all five: an audit failure blocks an operation only
where the audit record is the *point* of the operation being permitted.
A privileged bulk export whose start could not be recorded does not
happen. A key open whose decision could not be recorded does not
happen. Everything downstream of an already-determined outcome records
what it can.

LCS constructs the payload and attempts to enqueue it before
continuing past the audit point. It never waits for a userspace
consumer to observe or retain the event.
