---
title: Stalls and Loops
description: The failures that come from resolvd's single thread and its channel to netd — a reply that blocks the loop, a refused subscription, a lost registry watch, and a cache emptied by eviction.
---

## A client that does not read

Native replies and stub TCP replies are written from the loop, blocking,
for up to one second per write call, and a reply larger than the
socket's buffer takes several calls (§2.5). A local client that sends a
question whose reply is larger than its socket's buffer and then does
not read holds every door for those seconds: about two on the native
socket. Repeated, it slows every lookup on the machine. Nothing is
logged for a stub TCP write that times out; a native one logs
`control: reply failed`.

## netd refuses the subscription

When netd accepts the connection and answers `subscribe` with an error
— resolvd's account lacks `NETWORK_QUERY`, for instance — resolvd drops
the channel and reconnects half a second later, and the backoff never
grows (§3.2). The log shows `subscribed to netd`, then `netd refused the
subscription`, then `lost the netd channel; reconnecting`, about twice a
second, for as long as the refusal lasts. `resolv status` shows `netd`
as `not connected` except in the moment between each reconnection and
its refusal, and the scopes are whatever the last accepted snapshot
held, or none.

## The registry watch is lost

When the watch cannot be armed at startup, or fails and cannot be
re-armed, configuration changes are no longer seen (§2.3). `resolv
status` still shows the fallback servers in use, so a change to
`FallbackServers` that does not appear there is the sign. A restart
reads the key again and re-arms the watch.

## The cache empties itself

When the cache is full, storing an answer with a long lifetime evicts
every entry due to expire at least a second before it (§4.5). On a busy machine this shows
as `cache_entries` falling sharply after reaching 8 192, followed by a
burst of `upstream_sent` as the evicted names are asked again. Expired
entries are counted in `cache_entries` until they are evicted, so the
count reaching 8 192 does not mean 8 192 live answers.
