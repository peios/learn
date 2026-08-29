---
title: Conformance
description: Every requirement of this chapter collected by role — resolver, client, network manager, shim.
---

A conforming implementation MUST satisfy every requirement in this
chapter. This section collects them by role.

## Resolver obligations

### Doors

1. Offer the native socket, the stub listener and answer the shim, and
   run one resolution function behind all three (§6.3).
2. Offer no other policy path: no files, no in-shim DNS, no fallback
   (§6.3).

### Native channel

3. Frame as §6.4; refuse an oversized request without reading it, with
   an error reply (§6.4).
4. Ignore unknown keys; reject duplicate keys (§6.4).
5. One request per connection; bound the time a request may take to
   arrive (§6.4).
6. Access-check every request against the control object with the
   peer's real token; default Everyone `RESOLVER_QUERY`, SYSTEM and
   Administrators all (§6.4).
7. Answer unknown requests and denied requests with error replies
   (§6.4, §6.5).

### Outcomes

8. Never report `unavailable` as `notfound`; never cache `unavailable`
   (§6.6).
9. Report `unvalidated` until validating; never forward an upstream's
   `AD` (§6.6).

### Resolution

10. Route every question to exactly one scope, in the order of §6.7;
    never fan out.
11. Honour an exclusive scope absolutely while it is up (§6.7).
12. Expand single labels with applicable domains only; never send one
    bare; never expand a multi-label name; no `ndots` (§6.7).
13. Answer the synthetic names of §6.7 before any network; never
    forward `.local`; never speak LLMNR.
14. Key the cache by scope; flush a scope whose servers change or that
    goes away; cap TTLs as §6.A2 (§6.7).
15. Fresh source port, random identifier, 0x20 case with exact echo;
    ignore mismatched replies (§6.7).
16. EDNS0 with the §6.A2 buffer; TCP on truncation; demote failing
    servers; bounded attempts (§6.7).

### Stub door

17. Listen on `127.0.0.53` only, UDP and TCP; ignore non-loopback
    sources (§6.8).
18. Render outcomes as §6.8; CNAME from a bare question to its expanded
    name; `NOTIMP` and `FORMERR` as §6.8; truncate over the buffer.
19. Bind without privilege (§6.8).

### Network manager channel

20. Subscribe; replace scopes on every snapshot; reconnect with backoff;
    keep answering while disconnected (§6.9).
21. Read only `Machine\System\Network\Resolver` from the registry (§6.9).

## Network manager obligations

22. Answer `subscribe` with a snapshot and stream one on every change on
    the same connection (§6.9).
23. Send whole snapshots, never deltas; merge profile and lease facts
    itself (§6.9).

## Client obligations

24. Treat an error reply as "not answered", never as `notfound` (§6.5).
25. Be written against `validation` (§6.6).

## Shim obligations

26. One connection per libc call; answer `localhost` alone; `UNAVAIL`
    when the resolver is unreachable; `ERANGE` retry (§6.10).
27. No files, no DNS, no cache (§6.10).
28. Map outcomes as §6.10; never render `unavailable` as `NOTFOUND`.
