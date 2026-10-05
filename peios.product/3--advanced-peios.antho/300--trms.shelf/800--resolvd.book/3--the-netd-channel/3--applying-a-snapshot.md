---
title: Applying a Snapshot
description: How each snapshot becomes resolvd's hostname and scope list — the conversion of each field, what is dropped, and which cached answers are discarded.
---

Each snapshot replaces resolvd's scopes whole (PSPU §6.9). Applying one
has three parts: the hostname, the scope list, and the cache.

## The hostname

The snapshot's `hostname` is used when it is not empty. When it is
empty, resolvd reads the kernel's hostname at that moment; a kernel
hostname that is empty or `(none)` counts as none. [*netd-snapshot.empty-hostname-reads-kernel-hostname]

The result is parsed as a domain name. A name that does not parse, or
the root, leaves resolvd with no hostname: no synthetic answer is given
for it, and `status` reports an empty `hostname`. [*netd-snapshot.unparseable-hostname-is-no-hostname]

The kernel's hostname is otherwise read only at startup. A change to it
is not seen until the next snapshot with an empty `hostname`. [*netd-snapshot.kernel-hostname-read-only-at-snapshot-or-startup]

## The scope list

Each `DnsScope` in the snapshot becomes one scope, in snapshot order:

| Snapshot field | Becomes |
|---|---|
| `ifid` | The scope key [*netd-snapshot.ifid-is-scope-key] |
| `name` | The interface name reported in answers and in `status` [*netd-snapshot.name-is-reported-interface] |
| `servers` | Server addresses, in order. A string that is not an IP address is dropped. There is no port; servers are asked on port 53. [*netd-snapshot.servers-parsed-malformed-dropped] |
| `domains` | Search domains, in order. A string that does not parse as a name, and the root, are dropped. [*netd-snapshot.domains-parsed-malformed-dropped] |
| `addresses` | `(address, prefix length)` pairs. A string that is not `address/prefix` is dropped. [*netd-snapshot.addresses-parsed-malformed-dropped] |
| `default_route`, `exclusive`, `metric`, `level` | Carried as they are |
| `ntp` | Ignored |

Dropped entries are dropped silently. Every scope in the snapshot is
kept, whatever its level or server count; which of them take part in
routing is decided per question (§4.4). [*netd-snapshot.every-scope-kept]

resolvd then logs one line summarising the snapshot:

```text
netd: eth0: 1 server(s), 1 domain(s), default; wg0: 1 server(s), 0 domain(s)
```

with `, default` on each scope that claims the default route, or
`netd: no scopes` for an empty snapshot. [*netd-snapshot.summary-log-line]

## The cache

Comparing the new scope list with the old one, by scope key:

- a scope whose key is new loses any cached answers under that key; [*netd-snapshot.new-scope-key-flushed]
- a scope whose server list differs from before — in content or in
  order — loses its cached answers; [*netd-snapshot.changed-server-list-flushes-scope]
- a scope missing from the new snapshot loses its cached answers. [*netd-snapshot.missing-scope-flushed]

A change to a scope's domains, addresses, flags, metric or level leaves
its cache alone. [*netd-snapshot.other-changes-keep-cache] Demotion is kept per server address, not per scope,
and survives every snapshot (§4.6).

## Questions already in flight

A candidate is routed when it is first asked (§4.4), and its retries
stay with the scope it was routed to. When that scope's servers change,
retries use the new list; when the scope has gone, the next retry finds
no servers and the question ends `unavailable`. [*netd-snapshot.in-flight-retries-follow-scope-key] A transaction already
sent is not cancelled by a snapshot, and its reply is cached under the
scope key it was routed to. [*netd-snapshot.in-flight-reply-cached-after-flush]
