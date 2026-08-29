---
title: Three Doors, One Function
description: The native socket, the stub listener and the NSS shim — what each carries, who uses it, and the rule that every one of them runs the same resolution.
---

A resolver MUST offer three doors and MUST answer every question
through the same resolution function (§6.7) whichever door it arrived
by.

| Door | Callers | Carries |
|---|---|---|
| Native socket (§6.4) | Peios tools, the network manager, the NSS shim | Records with TTL, source, validation state; the caller's identity |
| Stub listener (§6.8) | Anything that speaks DNS itself — Go's `netgo`, musl, hickory | DNS; no caller identity |
| NSS shim (§6.10) | Everything via glibc `getaddrinfo` and `gethostbyname` | `struct hostent` / `gaih_addrtuple`, rendered from the native door |

The rule that matters is the second sentence. A bare `printer` arriving
at the stub door is expanded with the same search domains, routed to
the same scope and answered from the same cache as `printer` arriving on
the native socket. A static name from the registry is answered at every
door, so a program that never touches libc sees the same `printer` as
one that does. There is no configuration a door reads that another does
not, and no file behind any of them.

This is why there is no `/etc/hosts`: the stub answers static names
synthetically, so a direct-DNS resolver gets them without a file. And it
is why `/etc/resolv.conf` is a constant — `nameserver 127.0.0.53`,
`options edns0` — shipped by the resolver's package and never
regenerated: it is a pointer to the answerer, not a copy of the answer.
A search list in it would be a second expansion policy the resolver
could not see; there is none.

A resolver MUST NOT offer a fourth policy path — an in-process fallback
in the shim, a `files` source, a direct-DNS retry — behind any door.
Before the resolver is running, the shim answers `localhost` itself and
nothing else (§6.10).
