---
title: The Fd Store
description: Keeping file descriptors across a service's own restart — storing, removing, injecting and clearing them.
---

The fd store lets a service keep file descriptors across its own
restart. It pushes them to peinit, peinit holds them, and the new
process gets them back. That is what lets a stateful daemon — a web
server holding a listening socket, say — restart without dropping
connections it has already accepted.

`FdStoreMax` in the definition sets the maximum number of descriptors
peinit will hold. It defaults to **0**, which disables the store: most
services do not need it, and holding descriptors on behalf of a service
that will never ask for them back is pure cost.

## Storing

When an authenticated datagram carries `FDSTORE=1` with descriptors
attached:

1. If `FdStoreMax` is 0, peinit logs the rejection and **closes** the
   descriptor.
2. If the store already holds `FdStoreMax` entries, peinit logs the
   rejection and closes the descriptor. The existing store is not
   modified — a full store does not evict.
3. `FDNAME=<name>` names it; an absent or empty name means `stored`.
4. `FDPOLL=0` marks the descriptor exempt from poll monitoring.

Either rejection emits an `fd_store.rejected` event carrying the outcome
and the reason, so a service whose descriptors are being silently
dropped can find out why.

Several descriptors may share a name. One `FDSTORE=1` carrying N
descriptors creates N entries under the one name, each independently
subject to the limit — so the first few fit and the overflow is
rejected and closed.

peinit does not monitor stored descriptors. The `FDPOLL` flag is
recorded and nothing reads it, so no stored descriptor is evicted for
becoming invalid.

## Removing

`FDSTOREREMOVE=1` with `FDNAME=<name>` removes every descriptor of that
name and closes them. A name matching nothing is a no-op rather than an
error.

`FDSTOREREMOVE=1` **without** a name aborts the whole fd-store step for
that datagram — so a datagram carrying both an unnamed remove and an
`FDSTORE=1` performs neither, and the attached descriptors are dropped
and closed.

## Injecting

When a service restarts, peinit injects the stored descriptors during
the child's pre-exec path (§5.4):

1. They are placed consecutively from `SD_LISTEN_FDS_START` — descriptor
   3 — upward, with close-on-exec cleared: the only sanctioned
   exception to the close-on-exec discipline.
2. `LISTEN_FDS` is set to the count.
3. `LISTEN_FDNAMES` is set to a **colon-separated** list of names in the
   same order as the descriptor numbers.
4. The store is cleared. peinit no longer holds them.

Both variables are omitted entirely when the store is empty.
`LISTEN_PID`, which a conforming client checks against its own PID
before trusting `LISTEN_FDS`, is not set.

Injection happens for the main process only. Hooks and health checks
never receive stored descriptors.

The store is cleared on a successful injection, at the top of the
started-launch handling. A launch that *fails* does not clear it, so the
descriptors survive a failed attempt and are available to the next one.

## Clearing

The store is cleared, and its descriptors closed, when:

- **The service is stopped explicitly** — by an administrator, or by
  shutdown. The distinction peinit draws is the operation's type and
  source together: an administrator's stop clears, and a
  restart-policy-sourced stop does not. The service is not coming back
  from an explicit stop, so the descriptors are no longer useful.
- **The definition is removed** and its entry finally discarded (§3.8),
  immediately if nothing was running and on the instance's exit
  otherwise.

It **survives** an automatic restart — crash, restart policy, new start
— which is the entire point. The descriptors persist through exactly the
restart the service did not choose and cannot prepare for.

> [!NOTE]
> The `LISTEN_FDS` and `LISTEN_FDNAMES` convention is systemd's, so
> software already written to receive descriptors that way works
> unmodified. peinit's own C client library exposes the notification
> helpers but no descriptor-passing helper, so reaching the store from
> that library means constructing the control message by hand.
