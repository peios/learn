---
title: Failure Modes
order: 1
---

The registry spans a trust boundary (kernel ↔ userspace source).
Failure semantics MUST be explicit.

## Source crash

When a source process dies (connection closed unexpectedly):

1. **Hives marked unavailable.** Per-hive status set to Down.
2. **Pending requests fail** with EIO.
3. **Open key fds remain valid.** The fd holds a GUID and granted
   access mask, neither of which depends on the source. Operations
   requiring source round-trips (reads, writes, enumeration) return
   EIO while the source is unavailable.
4. **Transactions cancelled.** All open transactions scoped to that
   source are implicitly aborted.
5. **Watches remain armed.** Watch state is kernel-side and
   unaffected by source availability.

When the source restarts and re-registers:

- Hives marked Active.
- OVERFLOW delivered to every watch on keys in those hives.
- Existing fds resume working without re-opening.
- If a key's GUID no longer exists in the restarted source (e.g.,
  database restored from older backup), the first operation on
  that fd returns ENOENT.

## Request timeout

If a source does not respond within RequestTimeoutMs (default
30 seconds):

- LCS returns ETIMEDOUT to the caller.
- **The source stays alive.** A slow response is not a crash.
- When the source eventually responds, LCS processes the response
  normally (watch events dispatched for any mutations). The
  original caller is gone, so the response has no recipient.
- **Caller responsibility:** ETIMEDOUT means "may or may not have
  completed." Callers that need certainty MUST check state before
  retrying.

## Transaction timeout

If a transaction's lifetime timer fires:

- The transaction fd is closed (implicit abort).
- RSI_ABORT_TRANSACTION sent to the source.
- If a commit was in-flight and succeeds at the source before the
  abort takes effect, the writes are durable. The kernel has no
  transaction fd to deliver the response to. The late commit
  response is processed through the normal pipeline: watch events
  are dispatched for any mutations the source applied. Watchers
  may observe the effects of a timed-out transaction.
- **Caller responsibility:** transaction timeout means "may or may
  not have committed." Callers MUST check state before retrying.

## Source errors

Sources return errors from the defined vocabulary. LCS maps them
to errnos (see the Source Obligations section for the full error
table).

Source-specific error details are not exposed to callers. The
errno is the interface.

## Source data validation

LCS validates every response from a source before using it.

**Malformed data** (structurally valid RSI message, invalid
content):

- Request returns EIO to the caller.
- Audit event emitted (source, key GUID, validation failure
  description).
- Source stays alive. Corruption may be localised.

**Malformed protocol** (RSI message structurally invalid):

- Treated as a source crash. Connection torn down, hives marked
  unavailable.

## Fd lifecycle

Key fds and transaction fds are standard Linux file descriptors
subject to RLIMIT_NOFILE. No registry-specific fd leak protection
exists.

When a process exits, all fds are closed via normal kernel cleanup.
Key fds released, watches removed, transactions aborted.

## Layer deletion effects

Deleting a layer removes its path entries and value entries. Effects
on live state follow from the data model with no special cases:

- **Path entries removed.** Keys named only by the deleted layer
  become orphaned. Existing fds remain valid. Dropped when last fd
  closes.
- **Values surface.** Where the deleted layer had the
  highest-precedence entry, the next layer's value becomes
  effective.
- **Blanket tombstones removed.** Values previously masked by the
  deleted layer's blanket tombstone become visible.
- **SDs unchanged.** SD modifications are permanent (semantic
  rule 4).
- **Watches notified.** Appropriate events generated for all
  effective state changes.

## Memory bounding

Registry kernel memory is bounded by:

- **Watch queues:** per-queue max (NotificationQueueSize) ×
  per-process fd limit (RLIMIT_NOFILE).
- **Open key state:** per-fd overhead (GUID, granted mask, ancestor
  chain, watch state) × RLIMIT_NOFILE.
- **Layer table:** bounded by the number of layers (MaxLayersPerValue
  caps per-value resolution cost).
- **Pending RSI requests:** bounded by the number of threads blocked
  on registry syscalls, each with one in-flight request.

No registry-specific global memory cap is required. Standard Linux
resource limits provide sufficient protection.
