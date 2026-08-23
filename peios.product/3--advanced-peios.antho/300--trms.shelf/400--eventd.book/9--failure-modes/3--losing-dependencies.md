---
title: Losing Dependencies
description: Two of eventd's four dependencies can vanish after startup without stopping it — what survives, and what stops working.
---

Two of eventd's four dependencies can disappear after startup without
stopping it, and in both cases the ingestion path survives while the
query path does not. That asymmetry is deliberate: events that are not
collected are gone, and queries that cannot be answered can be asked
again.

## The registry becomes unavailable

If LCS or loregd goes away after eventd has started:

- eventd keeps its last known configuration. Changes are not applied
  until the registry returns.
- Descriptor lookups fall back to the cache. A pattern the cache does
  not hold is **denied**, fail-closed (§7.5).
- eventd keeps ingesting and keeps serving queries for descriptors it
  already resolved, indefinitely.
- When the registry returns, the watch fires and eventd re-reads.

This is a degraded state, not a failure. eventd does not exit, and it
does not stop collecting.

The related case is the **watch failing** while the registry is
otherwise reachable. eventd discards the descriptor cache and operates
fail-closed for new resolutions until the watch is re-established
(§7.5), because a cache it cannot trust to be current would make a
revocation silently ineffective. `SIGHUP` forces a configuration re-read
in the meantime (§8.3).

## KACS becomes unavailable

If KACS goes away after startup:

- `kacs_open_peer_token` fails on new query connections, so new queries
  are denied.
- `kacs_access_check` and `kacs_access_check_list` fail, so a query in
  progress that needs a fresh check is denied.
- Cached check results stay valid for the duration of the query that
  obtained them.
- **Event ingestion is unaffected.** Neither the drain nor the write
  path calls KACS (§8.1).
- Log and metric ingestion are unaffected.

eventd keeps collecting and cannot answer. Query service resumes when
KACS does.

## KMES

There is no partial mode. eventd attaches to every per-CPU ring buffer
at startup and fails to start if it cannot (§8.2); there is no
subsequent state in which KMES is present but unusable, because the
mapping is established once and the read protocol has no call that can
fail afterwards. A ring buffer resize is handled as a generation change,
not as a failure (§2.2).

## peinit

peinit supplies the boot ID at startup and manages the lifecycle. It has
no runtime role once eventd is running, so there is no failure mode
here — peinit going away means the system is going away.
