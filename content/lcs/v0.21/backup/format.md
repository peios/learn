---
title: Backup Format
order: 1
---

The standard registry backup format is used by REG_IOC_BACKUP and
REG_IOC_RESTORE, first-boot seeding, disaster recovery, and
offline migration. It is an LCS-level format -- sources never see
it. LCS serialises from source data on backup and deserialises into
RSI operations on restore.

## Design constraints

- **Streamable.** Written to an arbitrary fd (file, pipe, socket).
  No seeking. Single-pass write, single-pass read.
- **Full layer fidelity.** Every path entry, value, tombstone, and
  blanket tombstone is stored with its layer tag. Restoring
  reconstructs the full layered state.
- **Depth-first pre-order.** Parent keys appear before their
  children. Restore creates keys top-down without buffering.
- **SDs inline.** Each key record contains its full SD. No
  deduplication. External compression (e.g., piped through zstd)
  handles redundancy.
- **Self-verifying.** A trailer record contains an integrity check.
  Truncated or corrupted backups are detected at restore time.

## Versioning

The header contains two version fields:

- **Format version:** The version used to write the backup.
- **Minimum reader version:** The oldest reader that can correctly
  process this backup.

A writer using only older features sets a lower minimum reader
version, allowing older LCS implementations to restore the backup.
A reader encountering a minimum reader version higher than its own
MUST reject the backup.

## Record types

The stream is a sequence of typed records. Every record begins
with a common framing header:

| Field | Type | Description |
|---|---|---|
| record_type | uint16 | Record type code. |
| record_len | uint32 | Total record size in bytes, including this header (6 bytes minimum). Allows readers to skip unknown record types. |

The record payload follows immediately after the 6-byte framing
header.

### HEADER (record_type: 0x01)

First record. Exactly one. Payload:

| Field | Type | Description |
|---|---|---|
| Magic | 8 bytes | Fixed magic bytes identifying the format. |
| FormatVersion | uint32 | Format version of this backup. |
| MinReaderVersion | uint32 | Minimum reader version required. |
| Timestamp | int64 | Backup creation time (Unix nanoseconds). |
| RootGUID | GUID (16 bytes) | GUID of the key at the root of this backup. |
| HiveName | length-prefixed string | Which hive the backup was taken from. |

### LAYER (record_type: 0x02)

One per layer that has data in the subtree. Emitted after the
header and before any records that reference the layer. Payload:

| Field | Type | Description |
|---|---|---|
| Name | length-prefixed string | Layer identifier. |
| Precedence | uint32 | Layer precedence at time of backup. |
| Enabled | uint8 | 1 if enabled, 0 if disabled. |
| Owner | length-prefixed bytes | Owner SID (binary). |

### KEY (record_type: 0x03)

One per unique key object in the subtree, regardless of how many
layers name it. Payload:

| Field | Type | Description |
|---|---|---|
| GUID | GUID (16 bytes) | The key's unique identifier. |
| Flags | uint32 | Bit 0: volatile. Bit 1: symlink. |
| SDLength | uint32 | Length of the SD field in bytes. |
| SD | bytes | Full Security Descriptor. |
| LastWriteTime | int64 | Last modification time (Unix nanoseconds). |

Name and parent GUID are omitted -- they are derivable from the
PATH_ENTRY records that follow.

### PATH_ENTRY (record_type: 0x04)

One per name→key mapping per layer. Payload:

| Field | Type | Description |
|---|---|---|
| ParentGUID | GUID (16 bytes) | GUID of the parent key. |
| ChildName | length-prefixed string | Name under parent. |
| ChildGUID | GUID (16 bytes) | GUID of the key being named. GUID of all zeros indicates HIDDEN. |
| LayerName | length-prefixed string | Which layer this entry belongs to. |
| Sequence | uint64 | The entry's sequence number. |

### VALUE (record_type: 0x05)

One per value entry per layer, including tombstones. Payload:

| Field | Type | Description |
|---|---|---|
| KeyGUID | GUID (16 bytes) | Key this value belongs to. |
| Name | length-prefixed string | Value name (empty for default). |
| Type | uint32 | Registry type (REG_TOMBSTONE for tombstones). |
| DataLength | uint32 | Length of data field (0 for tombstones). |
| Data | bytes | Value data. |
| LayerName | length-prefixed string | Which layer this entry belongs to. |
| Sequence | uint64 | The entry's sequence number. |

### BLANKET_TOMBSTONE (record_type: 0x06)

One per blanket tombstone per layer. Payload:

| Field | Type | Description |
|---|---|---|
| KeyGUID | GUID (16 bytes) | Key this blanket tombstone belongs to. |
| LayerName | length-prefixed string | Which layer. |
| Sequence | uint64 | The entry's sequence number. |

### TRAILER (record_type: 0xFF)

Last record. Exactly one. Payload:

| Field | Type | Description |
|---|---|---|
| RecordCount | uint64 | Total number of records including header and trailer. |
| Checksum | 32 bytes | SHA-256 hash over all preceding bytes in the stream (from the start of HEADER to the end of RecordCount). |

## Stream ordering

```
HEADER                          (exactly one)
LAYER records                   (one per layer, before key data)
For each key in depth-first pre-order of the merged tree:
    KEY record                  (the key object)
    PATH_ENTRY records          (all layers' entries for this key)
    VALUE records               (all layers' values for this key)
    BLANKET_TOMBSTONE records   (all layers' blankets for this key)
    (recurse into children)
TRAILER                         (exactly one)
```

The merged tree is the union of all layers' namespaces. Depth-first
pre-order guarantees that a key's parent is always emitted before
the key itself.

**HIDDEN path entries.** A HIDDEN entry (ChildGUID = all zeros)
has no corresponding KEY record — it is a tombstone, not a key.
HIDDEN entries are emitted as PATH_ENTRY records under the parent
key's section in the stream. They appear alongside any GUID-bearing
path entries for the same (parent, child name). No KEY record is
emitted for the zero GUID. A HIDDEN entry that masks a path where
no real key exists in any layer is still a valid PATH_ENTRY record
— it expresses "this layer hides this name" regardless of whether
any other layer has a key there.

**Cross-layer path dependencies.** A path entry's parent GUID may
belong to a key that only has path entries in a different layer.
The merged tree walk handles this correctly.

## Restore semantics

Restore is a **replace** operation, not a merge. The target key's
entire subtree is removed before the backup contents are written.
The entire restore (teardown + rebuild) MUST be wrapped in a
single source transaction for atomicity. Sources that do not
support transactions MUST NOT be used as restore targets.

0. Begin a transaction on the source (RSI_BEGIN_TRANSACTION).
   Remove the target key's entire subtree by recursively
   deleting all descendant path entries, values, blanket
   tombstones, and key records via RSI operations within the
   transaction.
1. Read and validate HEADER (magic, minimum reader version).
2. Read LAYER records -- build layer context. If any layer has
   Precedence > 0 and the caller does not hold SeTcbPrivilege,
   abort the transaction and return EPERM.
3. For each KEY record in stream order (within the transaction):
   a. Create the key object in the source via RSI.
   b. Create PATH_ENTRY records via RSI.
   c. Create VALUE records via RSI.
   d. Create BLANKET_TOMBSTONE records via RSI.
4. Read TRAILER -- verify record count and checksum.
5. If checksum fails or GUID collision occurs, abort the
   transaction (all changes rolled back, including teardown).
6. Commit the transaction.

Depth-first pre-order ensures step 3 never encounters a parent
GUID that hasn't been created yet.

**ParentGUID validation.** LCS MUST validate every PATH_ENTRY
record's ParentGUID before issuing RSI_CREATE_ENTRY. The
ParentGUID MUST either be the restore target's root GUID or
appear in a KEY record already processed in the stream. If a
ParentGUID references a GUID outside the backup's key set, the
restore MUST be aborted with EINVAL. This prevents a crafted
backup from injecting path entries into arbitrary locations in
the existing namespace outside the restore subtree.

**GUID preservation.** The backup's GUIDs are written directly into
the target. If those GUIDs already exist elsewhere in the source,
restore fails. In practice, restore targets the same subtree the
backup was taken from (disaster recovery, rollback, first-boot
seed).

All record types use length-prefixed strings (uint32 length +
UTF-8 bytes) for variable-length fields, matching the RSI wire
format encoding defined in the RSI Wire Format appendix.
