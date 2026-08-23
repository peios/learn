---
title: Replication
type: concept
description: How UD replicates — multi-master convergence from per-atom merge stamps, the pull protocol with watermarks and up-to-dateness vectors, deterministic conflict repair, and rollback self-defence.
related:
  - universal-directory/concepts/objects-and-identity
  - universal-directory/concepts/persistence
  - universal-directory/the-console/the-debug-console
  - universal-directory/reference/json-api
---

UD is **multi-master and convergent**: every node accepts writes, nodes exchange state by pulling from each other, and any two nodes that have seen the same writes hold the same directory — regardless of the order the writes arrived. There is no primary, no write lock, and no repair coordinator.

Today the engine replicates between **in-process nodes**. The test fleet includes a seeded chaos simulation that asserts byte-equal convergence under partitions, clock skew, power loss, and hostile restores, with every node running the real [persistence](~universal-directory/concepts/persistence) path. A network transport for `udd`-to-`udd` sync is a later slice.

Everything on this page is engine behaviour you can observe through the [debug console](~universal-directory/the-console/the-debug-console).

## Nodes, invocations, and coordinates

Every node has a permanent **node id** and an **invocation id** naming one *incarnation of its database*. The node keeps a monotonic local **USN**, an update sequence number, and the pair `(invocationId, usn)` is the globally meaningful coordinate of a write.

A node that restores from backup re-mints its invocation id and lets the counter run on. The new id keeps old coordinates truthful, which is what makes restore survivable at all.

## Atoms and merge

Replication moves **merge atoms**: existence, placement, each attribute value, and the shred latch. Each carries a [stamp](~universal-directory/concepts/objects-and-identity).

Merging is per-atom, last-writer-wins by the stamp's total order — version, then timestamp, then origin. It is deterministic, so every node picks the same winner.

Three disciplines keep the merge honest:

- An apply that changes nothing — identical value *and* stamp — writes nothing, so duplicates die on arrival instead of echoing around the mesh.
- An equal value under a *stronger* stamp adopts the stamp, because future tiebreaks must agree everywhere.
- Replicated applies are **never re-validated**. A write that was legal at its origin always applies, even if this node's schema has not caught up. Conflicts are repaired, never refused.

The one refusal is the anomaly case: the same GUID arriving with a different class or system flag is two histories wearing one identity. The record is refused, the [journal](~universal-directory/the-console/the-debug-console) records it, and the sync cursor stalls so the refusal repeats until an operator intervenes. The engine never guesses.

## The pull protocol

A node syncs by **pulling**: *give me everything above my watermark*.

Per partner, keyed by invocation id, it remembers a **high-watermark** in the partner's local USN space. Alongside travels its **up-to-dateness vector** — per origin invocation, the highest coordinate it holds — which the sender uses for *dampening*: atoms the puller already covers are stripped from the stream, so data learned via a third node is never re-sent.

Answers come in chunks. A chunk with nothing to say still advances the watermark. Vectors only grow at a cleanly completed stream, never mid-flight, where a gap could be silently claimed.

A brand-new node **joins by pulling**. A zero watermark and an empty vector are the entire initial sync: the root is discovered from the records themselves, the schema compiles as definitions arrive — incomplete ones wait in [quarantine](~universal-directory/concepts/modifying-the-schema) — and objects whose class has not landed yet are *ghosts*, visible in the debugger, refusing writes, dissolving on convergence.

The pull handshake compares root GUIDs first. Different root, different domain, sync refused.

## Conflict repair is derived

Writes that were each legal at their origin can collide when merged. UD repairs these [as a view, never as a write](~universal-directory/concepts/objects-and-identity): colliding sibling names keep the *earliest* claim and CNF-display the later one, while orphans and broken move-cycles derive into `/LostAndFound`. Repairs dissolve the moment an ordinary write removes the violation.

Same atoms, same repair, on every node, with zero repair traffic.

## Deletion that replicates

The [three-stage lifecycle](~universal-directory/concepts/objects-and-identity) is built for merge.

Tombstones propagate as stamped existence transitions. A **shred** additionally sets a *latch* — a set-once atom that can never lose a race — so no concurrently written restore or edit can resurrect destroyed data anywhere. Aging, meaning the restore window and the purge horizon, is computed from stamps and the replicated config knobs, never raced via writes.

A node whose watermark predates knowledge its partner has already purged is refused with *full resync required*: wipe, re-mint, pull from zero, rather than silently missing deletes.

## Rollback self-defence

A node restored from a snapshot *without* re-minting — the classic VM-revert disaster — is detected from protocol evidence: a partner claiming this node's own stream beyond its own counter.

That claim takes either of two forms, and UD watches for both: an up-to-dateness **vector** entry, or a **watermark**. The bookmark survives even when the only transfer was an abandoned stream, where vectors never absorb. Evidence flows both ways, since requests carry the puller's watermark and chunks carry the sender's bookmark of the puller's stream back.

On detection the node latches. It re-mints its invocation, re-certifies its holdings into the new stream so nothing it wrote gets swallowed by dampening — with [persistence](~universal-directory/concepts/persistence), publishing the salvage as a live-store snapshot — suspends originating writes, and alarms. One clean pull then heals it.

Detection is strongest at first contact, and first contact is why the protocol has **probes**: a zero-record hello carrying only status. Applying chunks consumes local USNs, and every consumed USN burns a unit of evidence margin, so a restored node probes every reachable peer *before* applying or originating anything.

## Watching it happen

The console's header shows the node's identity, counter, and vectors. The **journal** tab shows every merge that discarded concurrent input, every refusal, every derived repair, and every rollback event.

Multi-master's classic sin is that lost updates are silent. UD's are not.
