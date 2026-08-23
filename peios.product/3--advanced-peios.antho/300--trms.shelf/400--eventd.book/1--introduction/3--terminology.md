---
title: Terminology
description: Terms this manual borrows unchanged from elsewhere in the corpus, and the ones it introduces.
---

Terms defined elsewhere are used with the same meaning and are not
redefined here: event, header, payload, stamp, ring buffer, consumer,
origin class and sequence number from the KMES chapters of the Peios
Kernel TRM and PSPK; token, GUID, SID, Security Descriptor, ACL, ACE and
privilege from the Peios Kernel TRM and PCDS; registry, hive, key, value
and layer from the Peios Kernel TRM; producer, client, log record,
metric sample, time series and concrete identifier from PSPU §3.2.

Syscall numbers and signatures for the kernel interfaces eventd calls —
`kmes_attach`, `kacs_open_peer_token`, `kacs_access_check` and
`kacs_access_check_list` — are in the Peios Kernel TRM's generated ABI
appendices, §2.A and §3.A. This manual names them and does not repeat
their numbers.

The following are specific to eventd.

**Drain thread**: one of the threads that reads from a per-CPU KMES ring
buffer. There is exactly one per CPU (§2.2).

**Writer thread**: the sole writer to one event shard. There is exactly
one per shard, and no other thread writes to that database (§2.3).

**Shard**: one of the independent SQLite databases the event store is
split across, each with its own file, write-ahead log and writer thread.
A shard is a write-path construct only; the query path treats the whole
directory as one store (§2.3).

**Active shard**: a shard in the current configuration's numbering.
**Historical shard**: a shard database left behind by a previous
configuration, opened read-only and still queried (§3.3).

**Handoff channel**: the bounded queue between drain threads and a
writer thread. It is a staging area for the current batch, not a buffer
(§2.3).

**Synthetic event**: a record eventd generates itself and writes
directly to a shard, bypassing KMES. Synthetic events carry no identity
stamps and no sequence numbers, and are distinguished by a
`synthetic.`-prefixed type (§2.6).

**Gap record**: the synthetic event recording that events were lost on
one CPU, and which sequence numbers went missing (§2.5).

**Event store directory**: the directory holding every shard database
and the metadata database. **Metadata database**: `eventd-meta.db`, the
one database that is not a shard and survives shard reconfiguration
(§3.5).

**Desired index set**: the global, priority-ordered list of fields eventd
aims to have indexed across all shards. **Material indexes**: the indexes a
given shard actually has, which converge toward the desired set when the
shard is quiet and diverge from it under pressure (§3.4).

**Shedding**: dropping secondary indexes to protect write throughput
(§3.4).

**Rollup**: a pre-computed metric aggregate for one series, one
function and one time window (§5.6). **Rollup registry**: the global set
of (function, window) pairs being pre-computed.

**Series cache**: the bounded in-memory map from series identity to
series row, which keeps metric ingestion off SQLite in the common case
(§5.3).

**Logical live size**: `(page_count - freelist_count) × page_size` for a
SQLite database — the space actually holding data, excluding pages freed
by deletion and available for reuse. Retention is enforced against this
rather than against the file size (§3.6).

**Quarantine**: renaming a database SQLite has reported corrupt, aside
from the path eventd uses, and creating an empty one in its place
(§3.3).
