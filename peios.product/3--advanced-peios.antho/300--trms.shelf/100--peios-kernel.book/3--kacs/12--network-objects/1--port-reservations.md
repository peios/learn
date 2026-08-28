---
title: Port Reservations
description: Binding a TCP or UDP port is an access check against a reservation — a security descriptor keyed by protocol and port range, read from the registry — not a privilege test against a port number.
---

Ports are a shared, unowned namespace. Linux protects it with one rule:
`bind(2)` below port 1024 needs `CAP_NET_BIND_SERVICE`, and everything
above is anyone's. That is too coarse in one direction — any privileged
process gets every low port — and absent in the other: nothing protects
8080, 3306 or 5432 from whichever process asks first.

On Peios the only thing worth authorising about a port is the **claim**
— binding a non-zero port — and it is authorised the way everything
else is: by a security descriptor. `CAP_NET_BIND_SERVICE` is in the
always-allow set (§3.10.2), so the Linux floor never refuses first, and
every claim reaches `security_socket_bind()`, where KACS decides.

The precedent is not Linux but HTTP.sys's URL reservations on Windows:
a sparse table of namespace prefixes, each carrying a descriptor,
consulted when a name is claimed, default-permissive where nothing is
reserved. This chapter moves that model down to the port layer.

## The object

A **reservation** is a selector mapped to a descriptor. The selector
names a set of protocols and an inclusive port range:

```
<proto>[,<proto>]:<lo>[-<hi>]      proto ∈ tcp | udp | *
```

`tcp:80`, `udp:53`, `tcp,udp:1-1023`, `*:8080`. Ports are decimal,
1–65535, no leading zeros, `lo <= hi`; a protocol may not repeat, so
every selector has one spelling. The address family is deliberately not
part of the selector: a reservation covers IPv4 and IPv6 alike, or
dual-stack squatting — claiming the v6 side of a port reserved on v4 —
would bypass it.

The rights are those of `<pkm/net.h>`:

| Right | Grants |
|---|---|
| `KACS_PORT_BIND` (`0x00000001`) | `bind(2)` to any port the selector contains |
| `READ_CONTROL` | reading the descriptor |

That is the whole mask. Editing a reservation is a registry write,
governed by the registry key's own descriptor — one edit policy for the
table — so `WRITE_DAC` and `WRITE_OWNER` inside a port descriptor mean
nothing and are never honoured. The generic mapping is `GENERIC_EXECUTE`
→ `PORT_BIND`, `GENERIC_READ` → `READ_CONTROL`, `GENERIC_WRITE` → nothing,
`GENERIC_ALL` → both.

## The table

Reservations live as **values** under one registry key:

```
Machine\System\Network\TcpIp\PortReservations\
    @                 REG_BINARY   SD     the default reservation
    tcp,udp:1-1023    REG_BINARY   SD
    tcp:80            REG_BINARY   SD
```

Each value's name is its selector and its data a self-relative
descriptor. The key's unnamed default value, `@`, is the **default
reservation**: the descriptor for every port no selector contains. The
shipped seed grants `PORT_BIND` to Everyone on `@` — an unreserved port
is anyone's, as on Windows — and to SYSTEM and the `bind-low-ports`
capability SID on `tcp,udp:1-1023`, which is the Linux convention
restated as policy. Services then carry their own entries:
`tcp:80,443 → NT SERVICE\httpd: PORT_BIND`, which composes with
per-service SIDs so that a compromised `sshd` cannot take 443 even
though both are "privileged".

The kernel reads the key whole and **rejects it whole**. Every name must
parse, every descriptor must parse, exactly one `@` must exist, and no
two selectors of equal width may overlap — the most specific match
would be ambiguous, and the kernel refuses to guess. On any failure the
load is audited and the previous table stays in force. Nested overlap,
and overlap between selectors of different widths, is how specificity
works and is accepted.

## The decision

At `bind(2)` on an `AF_INET` or `AF_INET6` socket whose protocol is TCP,
UDP or UDP-Lite:

1. If the requested port is 0 — ephemeral allocation — nothing is
   checked. Protocols no reservation covers (SCTP, raw) pass untouched.
2. The **most specific** reservation containing `(protocol, port)` is
   selected: the one covering the fewest ports, regardless of how many
   protocols it names. None → the default reservation.
3. The caller's effective token is evaluated against that descriptor
   for `PORT_BIND`, through the ordinary AccessCheck pipeline (§3.8)
   with PIP context, privilege-use marking and audit events — a port
   descriptor may carry a SACL, and its decisions surface through the
   same KMES stream as any other object's.
4. Deny → `-EACCES`. Grant → the bind proceeds, and the caller's token is
   recorded on the socket as its **binder**.

An explicit `bind(2)` before an outbound `connect(2)` meets the same
rule; it is not special-cased.

**Rebinding.** Binding onto a port that is already bound — with
`SO_REUSEADDR` or `SO_REUSEPORT` — is still a `bind(2)` and still meets
the reservation. The rule beyond that is that the new binder's user SID
must equal the existing binder's, or the caller must hold
`SeTcbPrivilege`: rebind is a property of the current binding, not of
policy, and a right on the reservation that let one principal rebind
onto another's port is a thing nothing legitimately needs. The binder
recorded on each socket is what makes that comparison local; the
comparison itself is applied where the stack resolves bind conflicts,
and Linux already applies the same-owner half of it for `SO_REUSEPORT`
by comparing the sockets' projected UIDs.

## Before the registry

The table comes from the registry through the same self-configuration
path LCS uses for its own limits (§5.10): read at the first source's
registration, then watched, so a change to the key is live without a
restart. Until the first successful load — early boot, or a registry
that never becomes available — a **compiled-in fallback** answers:
owner and group SYSTEM, one entry granting SYSTEM `PORT_BIND`, nobody
else. It is stricter than the shipped seed on purpose: nothing but
system components should be claiming ports before the registry exists.

The fallback is **replaced, never merged**. The moment the key loads it
is the sole authority; if a later load is rejected the last good table
stays, not the fallback. Effective policy therefore never depends on
boot timing.

## What this retired

`SeBindPrivilegedPortPrivilege` (bit 63) was the KACS privilege
`CAP_NET_BIND_SERVICE` mapped to before this object existed. A
reservation's grant is an ACE, and an ACE names a SID, not a privilege;
keeping the privilege would have been a second authorisation path
around the descriptor. It is retired and its bit is not reused. Low
ports are granted through the capability SID on the `1-1023`
reservation, which reaches a token by confinement — peinit for a
service, or positive confinement from the authority at logon for a
user.

## Tracing

Every decision emits `kacs:kacs_socket_bind` with reason `port-bind`:
`desired` carries `PORT_BIND`, `max_imp` carries the port, and `ret` the
verdict. Table loads emit reason `port-table`. See Appendix 3.C for the audit
events an evaluated descriptor's SACL can produce.
