---
title: The Network Manager Channel
description: How scopes reach the resolver — a subscribe request on the manager's control socket that streams a whole snapshot on every change — and why the registry is not the path.
---

The live facts of the network — which interface has which servers,
which carries the default route — never reach the resolver through the
registry, whatever the manager also records there. [*nri-manager.live-facts-never-in-registry] They
go from the network manager to the resolver directly, over the
manager's own control socket, and they are gone when the manager is.

## `subscribe`

The resolver connects to the manager's control socket
(`/run/netd/control.sock` on Peios; framing as §6.4) and sends
`{"query": "subscribe"}`, [*nri-manager.subscribe-request] which requires the manager's query right
(`NETWORK_QUERY`). [*nri-manager.subscribe-requires-network-query] The manager replies at once with a **snapshot** and
then keeps the connection open, sending a fresh snapshot every time the
picture changes, until either side closes. [*nri-manager.snapshot-at-once-then-on-every-change] This is the one request on
that socket that holds a connection. [*nri-manager.only-subscribe-holds-a-connection]

A snapshot is `ok: true`, `kind: snapshot`:

| Key | Type | Meaning |
|---|---|---|
| `hostname` | string | The machine's name as set by the manager; empty when unset [*nri-manager.snapshot-hostname] |
| `scopes` | array of map | One per managed interface with a link, in metric order [*nri-manager.snapshot-scopes-in-metric-order] |

Each scope:

| Key | Type | Meaning |
|---|---|---|
| `ifid` | string | The interface's stable identity; the cache scope key [*nri-manager.scope-ifid-is-cache-key] |
| `name` | string | The interface name |
| `servers` | array of string | The profile's static servers, then the lease's when the profile takes them [*nri-manager.scope-servers-order] |
| `domains` | array of string | The profile's search domains, then the lease's search list or domain [*nri-manager.scope-domains-order] |
| `addresses` | array of string | Every unicast address, CIDR form [*nri-manager.scope-addresses-cidr] |
| `default_route` | bool | The profile's `Dns.Default`; unset, whether the interface carries a default route [*nri-manager.scope-default-route] |
| `exclusive` | bool | The profile's `Dns.Exclusive` [*nri-manager.scope-exclusive] |
| `metric` | uint | The route metric [*nri-manager.scope-metric] |
| `level` | string | `link`, `addressed`, `routed` [*nri-manager.scope-level] |

A snapshot is the **whole** picture, not a delta. [*nri-manager.snapshot-is-whole-picture] It is a few hundred
bytes, and a whole picture cannot be misapplied out of order. The
resolver MUST replace its scopes with each snapshot; [*nri-manager.resolver-replaces-scopes] a scope whose
servers differ from before loses its cached answers (§6.7).

## Failure and reconnection

The manager MAY drop a subscriber it cannot write to. [*nri-manager.manager-drops-unwritable-subscriber] The resolver MUST
reconnect with backoff whenever the connection is lost or the manager
is absent, [*nri-manager.reconnect-with-backoff] and MUST keep answering meanwhile: synthetic names need no
scope, and the scopes it holds remain valid until replaced. [*nri-manager.keeps-answering-while-disconnected] A resolver
MUST NOT treat the manager's absence as a reason to refuse questions.

The manager merges the profile's static DNS keys with the lease itself;
the resolver reads `Profiles\` for nothing. [*nri-manager.resolver-never-reads-profiles] The registry keys the
resolver reads are exactly `Machine\System\Network\Dns` and its
subkeys; [*nri-manager.resolver-reads-only-dns-key] it MAY watch the parent `Machine\System\Network` so that the
key's creation is seen. When the manager reports no hostname the
resolver uses the kernel's. [*nri-manager.empty-hostname-uses-kernel]
