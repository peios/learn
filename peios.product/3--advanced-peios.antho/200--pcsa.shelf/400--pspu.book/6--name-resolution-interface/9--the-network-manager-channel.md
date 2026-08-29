---
title: The Network Manager Channel
description: How scopes reach the resolver — a subscribe request on the manager's control socket that streams a whole snapshot on every change — and why the registry is not the path.
---

The live facts of the network — which interface has which servers,
which carries the default route — never pass through the registry. They
go from the network manager to the resolver directly, over the
manager's own control socket, and they are gone when the manager is.

## `subscribe`

The resolver connects to the manager's control socket
(`/run/netd/control.sock` on Peios; framing as §6.4) and sends
`{"query": "subscribe"}`, which requires the manager's query right
(`NETWORK_QUERY`). The manager replies at once with a **snapshot** and
then keeps the connection open, sending a fresh snapshot every time the
picture changes, until either side closes. This is the one request on
that socket that holds a connection.

A snapshot is `ok: true`, `kind: snapshot`:

| Key | Type | Meaning |
|---|---|---|
| `hostname` | string | The machine's name as set by the manager; empty when unset |
| `scopes` | array of map | One per managed interface with a link, in metric order |

Each scope:

| Key | Type | Meaning |
|---|---|---|
| `ifid` | string | The interface's stable identity; the cache scope key |
| `name` | string | The interface name |
| `servers` | array of string | The profile's static servers, then the lease's when the profile takes them |
| `domains` | array of string | The profile's search domains, then the lease's search list or domain |
| `addresses` | array of string | Every unicast address, CIDR form |
| `default_route` | bool | The profile's `DNSDefaultRoute`; unset, whether the interface carries a default route |
| `exclusive` | bool | The profile's `DNSExclusive` |
| `metric` | uint | The route metric |
| `level` | string | `link`, `addressed`, `routed` |

A snapshot is the **whole** picture, not a delta. It is a few hundred
bytes, and a whole picture cannot be misapplied out of order. The
resolver MUST replace its scopes with each snapshot; a scope whose
servers differ from before loses its cached answers (§6.7).

## Failure and reconnection

The manager MAY drop a subscriber it cannot write to. The resolver MUST
reconnect with backoff whenever the connection is lost or the manager
is absent, and MUST keep answering meanwhile: synthetic names need no
scope, and the scopes it holds remain valid until replaced. A resolver
MUST NOT treat the manager's absence as a reason to refuse questions.

The manager merges the profile's static DNS keys with the lease itself;
the resolver reads `Profiles\` for nothing. The registry keys the
resolver reads are exactly `Machine\System\Network\Resolver` and its
subkeys; it MAY watch the parent `Machine\System\Network` so that the
key's creation is seen. When the manager reports no hostname the
resolver uses the kernel's.
