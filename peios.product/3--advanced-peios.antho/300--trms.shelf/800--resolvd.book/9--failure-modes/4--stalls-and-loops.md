---
title: Stalls and Loops
description: The failures that come from resolvd's single thread and its channel to netd — a stalled reply reader, a refused subscription, a lost registry watch, and a cache emptied by eviction.
---

## A client that does not read

Native and stub TCP replies are written without blocking (§2.5). A client
that does not read can retain its own queued reply until the fixed
one-second write deadline, then its connection closes. It does not stop
other lookups. Each door holds at most 256 queued replies; if full, a
new reply that cannot be written immediately is closed too. Stub TCP
write failures are silent; native failures log `control: reply failed`.

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
