---
title: The Stream
description: The streamable binary representation of a key and everything beneath it with full layer fidelity — what the design buys, and how it is versioned.
---

The registry backup format is a streamable binary representation of a
key and everything beneath it, with full layer fidelity. It is used by
`REG_IOC_BACKUP` and `REG_IOC_RESTORE`, by first-boot seeding, by
disaster recovery and by offline migration.

It is an **LCS-level** format. Sources never see it: LCS serialises
from source data on the way out and deserialises into RSI operations on
the way in.

Because a third party writes and reads these streams directly — that is
what migration and recovery mean — the format is a normative
specification rather than a description. It is a chapter of PSPK, and
every byte layout, record type, ordering rule and validation
requirement lives there. This section covers what LCS does with it.

## What the design buys

**Streamable.** It is written to an arbitrary fd — a file, a pipe, a
socket — with no seeking, in a single pass, and read back the same way.

**Full layer fidelity.** Every path entry, value, tombstone and blanket
tombstone is stored with its layer tag, so restoring reconstructs the
layered state rather than a flattened snapshot of it.

**Depth-first pre-order.** A parent always appears before its children,
so a restore can create keys top-down without buffering a tree.

**Descriptors inline.** Each key record carries its own descriptor with
no deduplication. Redundancy is external compression's problem; piping
through zstd handles it.

**Self-verifying.** A trailer carries a record count and a SHA-256 over
everything before it, so truncation and corruption are detected.

## Versioning

The header carries a format version and a **minimum reader version**. A
writer that used only older features sets a lower minimum, letting
older readers restore the stream; a reader that finds a minimum above
its own supported version rejects the stream outright, before touching
anything.

Both are 21 in the current implementation, and the reader supports 21.

Unknown record types are skipped when the minimum reader version allows
it, and they still count toward the record count and the checksum. A
writer that adds a record type a restore genuinely needs must raise the
minimum reader version, so that an older reader refuses the stream
rather than restoring an incomplete one.

Extension is by new **record types** only. Existing record payloads
must be consumed exactly; trailing bytes inside a known record are an
error. This is the opposite of the RSI's request convention (§5.8.4),
and the difference is deliberate: a stream is replayed into mutations
long after it was written, and a field silently ignored there is data
silently lost.
