---
title: The Stub Door
description: DNS on 127.0.0.53 — for programs that resolve without libc — and how outcomes, expansion and validation are rendered in DNS's terms.
---

A resolver MUST listen for DNS over UDP and TCP on `127.0.0.53` port 53
and MUST NOT listen on any other address: not `::1`, which a local DNS
server may legitimately want, and never a routable one. It MUST ignore
a datagram or connection whose source is not a loopback address.

The stub door exists for software that does not go through libc — a Go
binary built with `netgo`, a musl program, a Rust resolver library — and
it is non-optional: the constant `/etc/resolv.conf` points at it. It is
also anonymous: DNS carries no caller identity, and the door is not
governed by the control object. Everything on the machine may ask.

## Rendering

A query is answered by the same function as every other door (§6.7),
including search expansion of a single-label question. The reply is
rendered as:

| Outcome | Reply |
|---|---|
| `found` | `NOERROR`, the records in the answer section |
| `notfound` | `NXDOMAIN` |
| `unavailable` | `SERVFAIL` |

When the answer is at an expanded name, the reply's answer section
MUST begin with a `CNAME` from the question name to the expanded name,
so that a client checking names sees a well-formed chain. `RA` is set;
`AA` is not; `AD` is not, per §6.6.

A query with an opcode other than `QUERY` is answered `NOTIMP`; one
with other than exactly one question, or that cannot be decoded, is
answered `FORMERR` when there is enough of a header to echo. A reply
larger than the client's advertised buffer (or 512 bytes without EDNS)
is truncated with `TC` set; TCP carries the whole answer.

## Binding the port

Port 53 is below the privileged floor. On Peios the resolver's service
SID holds a port reservation for `tcp,udp:53`, shipped as a registry
seed by the resolver's package; the resolver needs no privilege to bind
it. A resolver MUST NOT require `SeTcbPrivilege` or any capability for
its listeners.
