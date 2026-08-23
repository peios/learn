---
title: Registry Events
description: The seven audit events LCS emits, which carry the caller summary, and which are audited unconditionally.
---

LCS emits **seven** audit events through KMES. Six of them carry the
caller summary (§2.3) rather than the subject record.

| Event | Emitted when |
|---|---|
| `LCS_KEY_OPEN_AUDIT` | A key open matched a SACL audit ACE. |
| `LCS_BACKUP_START` | Before `REG_IOC_BACKUP` reads any subtree data. |
| `LCS_BACKUP_COMPLETE` | After a backup completes, or fails after starting. |
| `LCS_RESTORE_START` | Before `REG_IOC_RESTORE` modifies any source state. |
| `LCS_RESTORE_COMPLETE` | After a restore completes, or fails after starting. |
| `LCS_SOURCE_VALIDATION_FAILURE` | LCS rejected malformed source data. |
| `LCS_SELF_CONFIG_INVALID` | LCS rejected an invalid self-configuration value. |

Every payload is a msgpack map with string keys. GUIDs are 16-byte
binary values; SIDs are binary KACS encodings.

## Backup and restore are audited unconditionally

Whatever the SACL on the target key says. They are privilege-gated bulk
operations that bypass per-key access checks entirely, so the audit
trail is the only record that they happened at all.

The start/complete pairing is deliberate too. `LCS_BACKUP_START` is
emitted *before* any data is read and `LCS_RESTORE_START` before any
state is modified, so an operation that dies partway still leaves
evidence that it began.

## Separately: watch records

LCS also produces **watch records**, read from a key file descriptor.
These are not KMES events, not msgpack, and not audit — see §5.4.
