---
title: Persistence
type: concept
description: How UD survives restarts — a RAM-resident store with a durability footprint on disk, generations of snapshots and write-ahead logs, blind-replay recovery, background compaction, and the disk-erasure guarantee behind shredding.
related:
  - universal-directory/concepts/replication
  - universal-directory/concepts/objects-and-identity
  - universal-directory/getting-started/running-udd
---

UD is **RAM-resident by design**. Every read and every merge runs against memory, and the disk exists for exactly one reason: so a node's state survives restarts.

This is the posture the directory world already runs in when healthy, made explicit. Active Directory's sizing guidance is RAM greater than or equal to the whole database; OpenLDAP's LMDB is a memory-mapped file; etcd caps its store at what mmap keeps resident. Scale-out comes from [replication](~universal-directory/concepts/replication) partitioning the tree across DCs, never from paging within one.

## Generations: snapshot plus write-ahead log

On disk lives a chain of **generations**. `snap-N` is the complete sorted state at the start of `wal-N`, and the WAL holds every change since as **state deltas** — the post-state of each touched atom, never logical operations, so replaying an old log can never depend on the code that wrote it.

One originating operation is one CRC-checksummed frame, and a subtree delete travels whole. One applied replication chunk is one frame. Every file opens with a self-checksummed, format-versioned header.

The encodings are hand-written, not derived. The disk format is a compatibility surface, and no struct rename may silently change bytes.

## Booting is blind replay

Load the newest valid snapshot, apply every later WAL frame with no merge logic and no clock reads, then recompute everything derived — the tree index, back-references, the compiled schema, structural repairs — exactly as a replication apply would.

A torn tail on the newest WAL is crash residue: nothing beyond it was ever acknowledged, and it truncates exactly. Damage anywhere else is corruption, and `udd` refuses to start rather than guess. That includes a torn sealed generation, valid frames *after* damage, and frames after a generation's closing seal.

## The durability contract

Nothing becomes visible to the outside before it is durable.

- A **mutating API call returns only after its frame is fsynced**. Concurrent writers share flushes through group commit, and the fsync never runs under the store lock.
- **Protocol speech is durable-gated.** Served records, chunk bookmarks, and advertised [up-to-dateness claims](~universal-directory/concepts/replication) never reference state a crash could erase. The deadly edge is a partner that *dampens* what you claim and can never resend it after your crash.
- A **failed fsync is fatal**, never retried. The daemon stops rather than acknowledge state the disk does not hold, and restart recovers to the last durable point.

Local reads may see RAM a few milliseconds ahead of the disk. No replication evidence ever does.

## Background compaction

Snapshots are produced by **rebuilding from the sealed files** — the recovery code path run ahead of time on a background thread — never by serialising the live store.

Rotation seals the active WAL, and the seal is durable before a successor exists. The rebuild replays the sealed chain, publishes the next snapshot atomically (write-temp, fsync, rename, fsync the directory), and only then deletes the generations it supersedes.

Recovery is therefore *production-exercised*: every compaction is a rehearsal of boot. Any mutation that forgot to write its delta shows up as a rebuild that disagrees with the live store, an invariant the test suite asserts continuously.

The one exception is the [rollback-salvage snapshot](~universal-directory/concepts/replication), which serialises the live store because the salvage exists only in RAM.

## Erasure reaches the disk

[Shredding](~universal-directory/concepts/objects-and-identity) destroys a payload in memory, but its bytes linger in older WAL frames and snapshots until compaction deletes those files.

That gap is managed as an explicit **erasure debt**. Every destructive transition starts a clock — a shred, a GC hardening, or an *applied* replicated shred, since the obligation follows the data rather than the command — and UD guarantees the destroyed payload has left the node's files **within two minutes** of the acknowledgment. In practice compaction kicks immediately; the window exists so a burst of shreds coalesces into one rebuild.

The debt is never written down. At boot it is re-derived from the replayed frames themselves, due immediately, so a node that dies mid-obligation finishes it promptly on restart.

The claim is deliberately scoped to the *filesystem*. What remains in unallocated blocks or an SSD's wear-levelled cells is the platform's concern, as it is for every directory product.

## Crashes, restores, and the sim

The persistence layer is torture-tested through a deterministic in-memory filesystem — torn writes at chosen bytes, failed fsyncs, power-loss simulation — and by the same [chaos simulation](~universal-directory/concepts/replication) that proved the merge.

Every simulated node runs on a faux disk through the real recovery path, crashes mid-anything, compacts under load, and is restored from forked disk images, the honest VM-revert. The fleet is still required to converge byte-for-byte at clear skies. A thin suite repeats the full lifecycle against a real filesystem.
