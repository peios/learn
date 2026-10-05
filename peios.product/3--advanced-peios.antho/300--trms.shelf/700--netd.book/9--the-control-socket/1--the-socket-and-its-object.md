---
title: The socket and its object
description: netd's control socket — its path and descriptors, the control object and its default descriptor, the access rights and their generic mapping, and how each connection is checked.
---

## The socket [*control.socket-path-and-descriptor]

netd listens on `/run/netd/control.sock`, a `SOCK_STREAM` Unix socket. At
startup it:

1. creates `/run/netd` if it is missing, sets its mode to `0755`, and
   gives it the descriptor below;
2. removes a socket file left by a previous run, logging `removed a stale
   /run/netd/control.sock`;
3. binds, sets the socket file's mode to `0666`, and gives it the same
   descriptor.

The descriptor on both: owner and group SYSTEM, and a DACL allowing SYSTEM
`GENERIC_ALL` and Everyone `GENERIC_READ | GENERIC_WRITE |
GENERIC_EXECUTE`. peinit creates `/run` SYSTEM-only and inheritable, so
without it nobody else could reach the socket. Everyone can connect; the
control object decides what each connection can do. A failure to set it is logged
as an error and netd carries on.

## The control object [*control.object-default-descriptor]

Every request is checked against the **control object**, a security
descriptor netd holds in memory. It is
`Machine\System\Network ControlSecurity`, a self-relative descriptor in a
`REG_BINARY` value, when that is set and valid. When it is not valid,
netd logs `ControlSecurity is not a valid descriptor (…); using the
default`.

The compiled default: owner and group SYSTEM, and a DACL of:

| Trustee | Rights |
|---|---|
| SYSTEM | `NETWORK_ALL_ACCESS` |
| Administrators | `NETWORK_ALL_ACCESS` |
| Everyone | `NETWORK_QUERY`, `READ_CONTROL` |

The object is rebuilt whenever the configuration changes (§2.3), so a
written `ControlSecurity` applies to the next connection.
[*control.object-follows-control-security]

## Rights [*control.rights-and-mapping]

| Right | Value |
|---|---|
| `NETWORK_QUERY` | `0x00000001` |
| `NETWORK_CONTROL` | `0x00000002` |
| `NETWORK_ALL_ACCESS` | `0x000F0003`: both, plus the standard rights |

The generic mapping:

| Generic right | Maps to |
|---|---|
| read | `NETWORK_QUERY`, `READ_CONTROL` |
| write | `NETWORK_CONTROL`, `READ_CONTROL` |
| execute | `NETWORK_QUERY` |
| all | `NETWORK_ALL_ACCESS` |

## The check [*control.access-check-on-peer-token]

For each request, netd opens the connecting peer's token through KACS and
runs a real access check of the request's right (§9.2) against the
control object. It never looks at `SO_PEERCRED`, so a deny-only group or
a filtered token is judged as the kernel would judge it anywhere else. A
peer whose token cannot be opened is denied.

A denied request is answered `{ok: false, error: "access denied"}`, and
nothing else happens.

## One connection at a time [*control.serial-and-blocking]

The control socket is served on netd's one thread (§2.2). When the
listener is readable, netd accepts and serves connections one after
another until no more are waiting. Each accepted connection gets a read
timeout and a write timeout of 2 s. A peer that connects and sends
nothing therefore holds netd's whole loop for 2 s, and one that keeps
connections arriving keeps netd serving them. No DHCP or router-discovery
timer fires and no kernel event is read in the meantime.
