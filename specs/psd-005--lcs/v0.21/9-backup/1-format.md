---
title: Backup Format
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

Forward-compatible writers MUST raise MinReaderVersion when a new
record type is required for correct restore. If MinReaderVersion is
less than or equal to the reader's supported version, unknown record
types are treated as optional extension records and skipped as
described below.

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
| RootGUID | GUID (16 bytes) | GUID of the key at the root of this backup. On restore, this GUID is remapped to the already-open restore target key. |
| HiveName | length-prefixed string | Which hive the backup was taken from. |

### LAYER manifest (record_type: 0x02)

One per layer name that has layer-tagged data in the subtree.
Emitted after the header and before any records that reference the
layer. A LAYER record is a stream manifest entry, not an
authoritative backup of the global layer metadata key under
`Machine\System\Registry\Layers\<LayerName>\`. Full backup of a
layer definition occurs only when that metadata subtree is itself
inside the backed-up registry subtree and is therefore represented by
ordinary KEY, VALUE, PATH_ENTRY, and SD data. Payload:

| Field | Type | Description |
|---|---|---|
| Name | length-prefixed string | Layer identifier. |
| Precedence | uint32 | Layer precedence observed at backup time, used for restore validation only. |
| Enabled | uint8 | Enabled state observed at backup time, used for restore validation only. Must be 0 or 1. |
| Owner | length-prefixed bytes | Owner SID (binary) observed at backup time, used for restore validation only. |

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
LAYER manifest records          (one per referenced layer, before key data)
For each key in depth-first pre-order of the merged tree:
    KEY record                  (the key object)
    PATH_ENTRY records          (all layers' entries for this key)
    VALUE records               (all layers' values for this key)
    BLANKET_TOMBSTONE records   (all layers' blankets for this key)
    (recurse into children)
TRAILER                         (exactly one)
```

Unknown record types MAY appear after HEADER and before TRAILER.
They are ignored for stream ordering: they do not start or end a key
section, do not satisfy required records, do not contribute layer
manifest declarations, and do not affect root mapping, sequence
remapping, or restore validation except through the common framing,
RecordCount, and checksum rules. Records after TRAILER are invalid.

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
contents and descendants are removed before the backup contents are
written. The target key object itself is not deleted or replaced:
its GUID, parent, name, volatile flag, and symlink flag remain the
restore root identity.
The entire restore (teardown + rebuild) MUST be wrapped in a
single read-write source transaction for atomicity. Sources that do
not support RSI_BEGIN_TRANSACTION with mode RSI_TXN_READ_WRITE MUST
NOT be used as restore targets.

## Restore root mapping

The backup HEADER RootGUID is a stream-local identity for the
backup root. REG_IOC_RESTORE is invoked on an already-open target
key fd, and that target key remains the root object after restore.
LCS MUST remap every reference to HEADER.RootGUID in the backup
stream to the target key's existing GUID before validating
ParentGUID references or issuing RSI operations.

The backup stream MUST contain exactly one KEY record whose GUID is
HEADER.RootGUID. That KEY record supplies the restore root's mutable
state: security descriptor and last write time. LCS MUST write those
mutable fields to the target key with RSI_WRITE_KEY inside the
restore transaction. The root KEY record's immutable flags MUST
match the target key's existing immutable flags. If the backup root
volatile or symlink flag conflicts with the target key's volatile or
symlink flag, restore fails with EINVAL.

The target key's GUID, parent, and name are never taken from the
backup stream. The backup root GUID is not created as a new key
record. Descendant KEY records keep their backup GUIDs after root
remapping. Duplicate non-root GUIDs inside the stream are invalid.
A non-root GUID that already exists outside the subtree being
replaced is a GUID collision and fails with EEXIST.

0. Begin a read-write transaction on the source
   (RSI_BEGIN_TRANSACTION with mode RSI_TXN_READ_WRITE).
1. Read and validate HEADER (magic, minimum reader version).
2. Read LAYER manifest records and build restore layer context. If
   any declared layer has Precedence > 0, or any existing cached
   layer table entry for the same folded identity has Precedence >
   0, and the caller does not hold SeTcbPrivilege, abort the
   transaction and return EPERM.
3. Read and validate the root KEY record for HEADER.RootGUID.
   Verify the immutable flag rules above. Remove the target key's
   contents and descendants by recursively deleting descendant path
   entries, root and descendant value entries, root and descendant
   blanket tombstones, and descendant key records via RSI operations
   within the transaction.
4. Write the root KEY record's mutable fields to the target key via
   RSI_WRITE_KEY.
5. Process the root record section's VALUE and BLANKET_TOMBSTONE
   records via RSI after applying the root GUID remapping to
   KeyGUID and sequence remapping. The backup root's incoming
   PATH_ENTRY records are not restored; the target key's existing
   incoming path entries remain authoritative for the restore root.
6. For each non-root KEY record in stream order (within the
   transaction):
   a. Buffer that KEY section's PATH_ENTRY records. To create the
      key object, LCS selects the first GUID-bearing PATH_ENTRY in
      stream order whose ChildGUID, after HEADER.RootGUID -> target
      GUID remapping, equals the KEY record's GUID. That path entry's
      remapped ParentGUID and child name are the RSI_CREATE_KEY
      parent/name anchor. If no such path entry exists, or if any
      PATH_ENTRY in a non-root KEY section is HIDDEN or targets a
      different GUID after remapping, restore fails with EINVAL.
      ParentGUID validation still applies before the create is
      issued. LCS then issues RSI_CREATE_KEY using the KEY record's
      GUID, SD, volatile flag, symlink flag, and the selected
      parent/name anchor. Immediately after successful
      RSI_CREATE_KEY, LCS writes the KEY record's LastWriteTime to
      that key with RSI_WRITE_KEY before replaying the section's
      PATH_ENTRY, VALUE, or BLANKET_TOMBSTONE records.
   b. Create PATH_ENTRY records via RSI, after applying the
      HEADER.RootGUID -> target GUID remapping to ParentGUID and
      ChildGUID fields and sequence remapping.
   c. Create VALUE records via RSI, after applying the root GUID
      remapping to KeyGUID and sequence remapping.
   d. Create BLANKET_TOMBSTONE records via RSI, after applying the
      root GUID remapping to KeyGUID and sequence remapping.
7. Read TRAILER -- verify record count and checksum.
8. If checksum fails or GUID collision occurs, abort the
   transaction (all changes rolled back, including teardown).
9. Commit the transaction.

Depth-first pre-order ensures restore never encounters a parent
GUID that hasn't been created yet.

**ParentGUID validation.** LCS MUST apply root remapping and then
validate every PATH_ENTRY record's ParentGUID before issuing
RSI_CREATE_ENTRY. The remapped ParentGUID MUST either be the restore
target's root GUID or appear in a non-root KEY record already
processed in the stream. If a ParentGUID references a GUID outside
the backup's remapped key set, the restore MUST be aborted with
EINVAL. This prevents a crafted backup from injecting path entries
into arbitrary locations in the existing namespace outside the
restore subtree.

**GUID preservation.** Except for HEADER.RootGUID, the backup's
GUIDs are written directly into the target. If a non-root backup
GUID already exists elsewhere in the source outside the replaced
subtree, restore fails with EEXIST. In practice, restore often
targets the same subtree the backup was taken from (disaster
recovery, rollback, first-boot seed), but it is also valid to restore
a backup into a different already-created target key.

**Layer manifest validation.** LCS MUST validate LAYER records
before processing KEY records:

- every layer name must be valid under the normal layer-name rules;
- folded layer identities must be unique within the manifest;
- Enabled must be 0 or 1;
- Owner must be a parseable SID;
- every PATH_ENTRY, VALUE, and BLANKET_TOMBSTONE layer name in the
  stream must have exactly one corresponding LAYER manifest record.

LAYER manifest records do not create, update, delete, enable,
disable, or authorize global layer metadata. If restored entries
reference a layer absent from the current in-memory layer table and
the restore stream does not also restore the corresponding
`Machine\System\Registry\Layers\<LayerName>\` metadata subtree as
ordinary registry data, those entries become latent unknown-layer
entries under §2.7 and are ignored during resolution until real
layer metadata exists. If the metadata subtree is included in the
backup, it is restored through the normal KEY/VALUE/SD restore path;
those ordinary records, not the LAYER manifest, define the layer.

**Sequence remapping.** Backup sequence numbers preserve the
backup's internal layer-resolution ordering, but restore is a new
mutation. Restored layer-qualified records MUST become newer than
pre-restore entries while preserving their relative ordering from
the backup stream. LCS therefore MUST NOT write backup sequence
numbers directly.

Sequence remapping MUST preserve the backup format's streamability:
LCS MUST NOT require a seekable input fd or a full pre-scan of the
backup stream. Before dispatching the first restored
layer-qualified record, LCS acquires the global sequence-allocation
gate and records `restore_sequence_offset = next_sequence`. LCS
holds this gate until the restore transaction reaches a terminal
state. Other sequence-allocating registry mutations wait while the
gate is held; registry reads are not blocked by this gate. If there
are no restored layer-qualified records, LCS need not acquire the
gate.

For every restored layer-qualified record:

```
new_sequence = restore_sequence_offset + backup_sequence
```

If the addition would overflow uint64, restore fails with EOVERFLOW
before dispatching that record. LCS tracks the largest
`new_sequence` it has dispatched. When the restore transaction
commits, aborts, fails, or is cancelled because of source teardown,
LCS advances `next_sequence` to at least `max_dispatched_sequence +
1` before releasing the sequence-allocation gate. It does not roll
this advancement back if the restore aborts; dispatched restore
sequence numbers become unused gaps just like failed normal writes.

LCS sends `new_sequence` in the RSI write for each restored record.
Restore dispatch order remains structural stream order; the remapped
sequence numbers, not dispatch order, preserve the backup's internal
layer-resolution order. This uses the restore path's explicit RSI
sequence field and intentionally bypasses the ordinary
single-number allocation helper used by normal writes. While the
sequence-allocation gate is held, these explicit restore sequence
numbers are treated as allocated by LCS even though `next_sequence`
is advanced past them only when the restore transaction reaches a
terminal state.

**Unknown records.** Restore MUST skip unknown record types when
HEADER.MinReaderVersion is less than or equal to the reader's
supported backup format version. Before skipping, LCS MUST validate
that `record_len >= 6` and that the record body can be read in full.
Skipped records remain part of the backup stream for TRAILER
RecordCount and checksum verification. If an unknown record is
semantically required for correct restore, the writer MUST set
MinReaderVersion higher than v0.21 so v0.21 readers reject the
backup before mutation.

All record types use length-prefixed strings (uint32 length +
UTF-8 bytes) for variable-length fields, matching the RSI wire
format encoding defined in §11.3.
