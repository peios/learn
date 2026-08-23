---
title: Records
description: Every record type in wire order — HEADER, LAYER, KEY, PATH_ENTRY, VALUE, BLANKET_TOMBSTONE and TRAILER.
---

Payload fields are listed in wire order, immediately after the six-byte
framing header, with no padding between them.

## `HEADER` — `0x01`

Exactly one, first in the stream. Fixed portion 44 bytes plus the hive
name.

| Size | Field | Description |
|---|---|---|
| 8 | `Magic` | The ASCII bytes `PEIOSREG` — `50 45 49 4F 53 52 45 47`. |
| 4 | `FormatVersion` | `u32`. |
| 4 | `MinReaderVersion` | `u32`. |
| 8 | `Timestamp` | `i64`, Unix nanoseconds. |
| 16 | `RootGUID` | The GUID of the key at the root of this backup. |
| 4+n | `HiveName` | The hive the backup was taken from. |

A reader MUST reject a stream whose magic does not match, and MUST
reject one whose `MinReaderVersion` exceeds its own supported version.

`HiveName` MUST be a valid hive name under the ordinary naming rules.

`RootGUID` is a **stream-local** identity for the backup root. On
restore it is remapped to the target key (§5.4).

## `LAYER` — `0x02`

One per layer name that has layer-tagged data anywhere in the stream.
All `LAYER` records precede all key data.

| Size | Field | Description |
|---|---|---|
| 4+n | `Name` | The layer name. |
| 4 | `Precedence` | `u32`, as observed at backup time. |
| 1 | `Enabled` | `u8`. MUST be 0 or 1. |
| 4+n | `Owner` | Binary SID, as observed at backup time. |

A `LAYER` record is a **stream manifest entry**, not a backup of the
layer's definition. It records what the layer looked like when the
backup was taken so that a restore can validate the stream against it,
and it creates, updates, deletes, enables, disables and authorises
nothing.

A layer's definition is backed up only when its metadata subtree is
itself inside the exported subtree, in which case it appears as
ordinary `KEY`, `PATH_ENTRY` and `VALUE` records like anything else.

A reader MUST validate that every layer name is valid, that folded
layer identities are unique within the manifest, that `Enabled` is 0 or
1, that `Owner` parses as a SID, and that **every** layer name
appearing in a `PATH_ENTRY`, `VALUE` or `BLANKET_TOMBSTONE` has exactly
one corresponding `LAYER` record.

## `KEY` — `0x03`

One per distinct key object in the subtree, however many layers name
it.

| Size | Field | Description |
|---|---|---|
| 16 | `GUID` | The key's identity. MUST NOT be nil. |
| 4 | `Flags` | `u32`. Bit 0 volatile, bit 1 symlink. |
| 4 | `SDLength` | `u32`. |
| n | `SD` | The full Security Descriptor. |
| 8 | `LastWriteTime` | `i64`, Unix nanoseconds. |

Name and parent GUID are **absent**. They are derivable from the
`PATH_ENTRY` records in the key's own section, and carrying them
separately would let a stream contradict itself.

Undefined bits in `Flags` MUST be zero. A reader MUST reject a record
with any bit outside `0x03` set, rather than ignoring it.

`SD` MUST parse as a Security Descriptor and MUST have an owner.

## `PATH_ENTRY` — `0x04`

One per name-to-key mapping per layer.

| Size | Field | Description |
|---|---|---|
| 16 | `ParentGUID` | The parent key. MUST NOT be nil. |
| 4+n | `ChildName` | The name under that parent. |
| 16 | `ChildGUID` | The key being named, or an **all-zero GUID** meaning HIDDEN. |
| 4+n | `LayerName` | The layer this entry belongs to. |
| 8 | `Sequence` | `u64`. |

`ChildGUID` is the only GUID field in the format that may be nil, and a
nil one means HIDDEN rather than "no key". No `KEY` record is emitted
for the zero GUID.

## `VALUE` — `0x05`

One per value entry per layer, tombstones included.

| Size | Field | Description |
|---|---|---|
| 16 | `KeyGUID` | The key this value belongs to. MUST NOT be nil. |
| 4+n | `Name` | The value name; empty for the default value. |
| 4 | `Type` | `u32`. |
| 4 | `DataLength` | `u32`. |
| n | `Data` | The value's bytes. |
| 4+n | `LayerName` | The layer this entry belongs to. |
| 8 | `Sequence` | `u64`. |

`Type` MUST be one of the defined registry value types, or
`REG_TOMBSTONE` (`0xFFFF`). A tombstone MUST carry zero-length data.

## `BLANKET_TOMBSTONE` — `0x06`

One per blanket tombstone per layer.

| Size | Field | Description |
|---|---|---|
| 16 | `KeyGUID` | The key this blanket belongs to. MUST NOT be nil. |
| 4+n | `LayerName` | The layer. |
| 8 | `Sequence` | `u64`. |

## `TRAILER` — `0xFF`

Exactly one, last. Payload 40 bytes, so the whole record is 46.

| Size | Field | Description |
|---|---|---|
| 8 | `RecordCount` | `u64`. Every record in the stream, `HEADER` and `TRAILER` included. |
| 32 | `Checksum` | SHA-256. |

`RecordCount` MUST be at least 2 — a stream has at minimum a header and
a trailer.

### What the checksum covers

The checksum is a SHA-256 over the bytes from the **start of the
`HEADER` record's framing header** through the **end of
`TRAILER.RecordCount`**, inclusive.

That is: every byte of every preceding record, then the trailer's own
six-byte framing header, then the eight bytes of `RecordCount`. The 32
checksum bytes themselves are not covered, and nothing follows them.

Skipped unknown records are covered, in full, like any other.

A reader MUST verify both `RecordCount` and `Checksum`. A stream whose
record count does not match, or whose checksum does not verify, MUST be
rejected.
