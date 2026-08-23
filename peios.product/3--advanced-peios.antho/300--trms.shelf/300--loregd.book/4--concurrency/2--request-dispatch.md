---
title: Request Dispatch
description: RSI requests arrive multiplexed on one descriptor — identifying the target hive, and the operations that resolve differently.
---

RSI requests arrive multiplexed on the `/dev/pkm_registry` file
descriptor. Each carries a request id and a transaction id in its header.

loregd reads messages into a single 16 MiB buffer, copies each one out,
and hands it to a **new goroutine** — one per request, with no cap on how
many may be in flight. Responses are serialised by a mutex, because one
write to the device must correspond to exactly one response. On shutdown
the in-flight goroutines are drained before the process exits.

## Identifying the target hive

Most operations name a key GUID (or, for lookups and enumerations, a
parent GUID), and loregd must decide which hive owns it.

A `guidCache` maps GUID to hive. It is seeded at startup with every
hive's root GUID, and maintained as keys come and go:

- `RSI_CREATE_KEY` stores the new GUID **immediately**, before the
  transaction that created it commits, and registers an abort hook to
  evict it if that transaction rolls back. The immediate store is
  necessary because the cache-miss probe reads through the pool, which
  cannot see uncommitted rows.
- `RSI_DROP_KEY` evicts immediately outside a transaction, or through a
  commit hook inside one.
- `RSI_DELETE_LAYER` evicts the GUIDs its deletion orphaned.

On a miss, loregd probes each hive in turn:

```sql
SELECT 1 FROM main.keys WHERE guid = ?
UNION ALL
SELECT 1 FROM volatile.keys WHERE guid = ?
LIMIT 1
```

Only hits are cached, so a GUID that exists nowhere is re-probed against
every hive on every request that names it. The cache has no size bound;
it shrinks only through the three eviction paths above.

A GUID that resolves to no hive produces `RSI_NOT_FOUND` for most
operations. `RSI_DROP_KEY` and the entry deletions treat it differently —
see §5.3 and §5.4.

## Operations that resolve differently

`RSI_FLUSH` carries a hive **name** rather than a GUID and resolves it by
folded name (§3.4), so the match is case-insensitive.

`RSI_DELETE_LAYER` does not resolve a hive at all: it applies to every
registered hive and concatenates the orphan sets (§5.6).
