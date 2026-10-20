---
title: Scope and Roles
description: The byte stream representing a registry key and everything beneath it with full layer fidelity, its two roles, and the constraints that shaped it.
---

This chapter specifies the **registry backup format**: the byte stream
that represents a registry key and everything beneath it, with full
layer fidelity.

Two roles participate, and unlike a live protocol they need not exist
at the same time.

The **writer** produces a stream. The Peios kernel's registry subsystem
is one writer; so is any third-party tool that constructs a backup for
migration, provisioning or archival.

The **reader** consumes one. The kernel is a reader, and so is any tool
that inspects, converts or transforms a backup.

The format is specified rather than described because both roles are
publicly implementable, and because a stream outlives the process that
wrote it. A backup taken on one machine is restored on another, by a
different implementation, perhaps years later.

This chapter covers:

- the framing common to every record, and the encoding of its fields
- the versioning fields, and the rules under which the format may be
  extended
- every record type and its payload, in wire order
- the ordering of records within a stream
- the integrity trailer and exactly what it covers
- what a reader MUST validate, and what a restore MUST do with a
  stream it accepts

This chapter does not cover:

- The registry data model the stream represents — hives, keys, layers,
  tombstones, resolution — which is described in the Peios Kernel TRM.
- The Registry Source Interface, which is a separate chapter. The
  backup format is a kernel-level format; a registry source never sees
  one.
- The system calls that produce and consume a stream.
- The binary layout of a Security Descriptor or a SID, which is
  defined in PCDS. A backup carries them as opaque byte strings.

## Design constraints

The format is shaped by five requirements, and an implementation of
either role has to respect all of them.

**Streamable.** A stream is written to an arbitrary descriptor — a
file, a pipe, a socket — in a single forward pass, and read back the
same way. Neither role may require seeking.

**Full layer fidelity.** Every path entry, value, tombstone and blanket
tombstone carries its layer tag. Restoring reconstructs the layered
state, not a flattened view of it.

**Depth-first pre-order.** A key's parent always appears before it, so
a reader can create keys top-down without buffering a tree.

**Descriptors inline.** Each key record carries its own Security
Descriptor, with no deduplication and no shared table. Redundancy is
left to external compression.

**Self-verifying.** A trailer carries a record count and a
cryptographic checksum, so truncation and corruption are detectable
before anything is acted on.
