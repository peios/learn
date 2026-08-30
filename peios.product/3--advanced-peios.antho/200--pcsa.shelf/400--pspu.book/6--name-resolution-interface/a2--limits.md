---
title: Limits
description: The mainline values for every bound in this chapter.
---

| Bound | Mainline | Defined in |
|---|---|---|
| Message ceiling, native channel | 65 536 bytes | §6.4 |
| Request delivery bound, native channel | 5 s | §6.4 |
| Per-server timeout | 2 s | §6.7 |
| Attempts per question | 3 | §6.7 |
| Demotion period | 30 s | §6.7 |
| Positive TTL cap | 86 400 s | §6.7 |
| Negative TTL cap | 300 s | §6.7 |
| EDNS0 buffer advertised | 1 232 bytes | §6.7 |
| Upstream transactions in flight (synthetic and cached answers are never refused) | 4 096 | §6.7 |
| Native connections still delivering a request | 256 | §6.4 |
| Stub TCP clients held at once | 256 | §6.8 |
| Cache entries | 8 192 | §6.7 |
| Stub TCP client bound | 10 s | §6.8 |
| Manager reconnect backoff | 0.5 s doubling to 10 s | §6.9 |

An implementation MAY adjust these; it MUST document the values it
uses. The relations that must hold: the shim's own timeout exceeds
attempts × per-server timeout, so a slow upstream is reported by the
resolver as `unavailable` rather than by the shim as a timeout.
