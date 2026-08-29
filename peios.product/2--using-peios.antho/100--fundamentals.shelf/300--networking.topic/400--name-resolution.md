---
title: Name resolution
type: concept
description: How a Peios machine turns names into addresses — resolvd answers every program through one policy, per-interface servers come from netd, static names live in the registry, and there is no /etc/hosts.
related:
  - peios/networking/overview
  - peios/networking/configuring-profiles
  - peios/linux-compatibility/name-service-switch
  - peios/name-resolution-interface/scope-and-roles
---

Every name a program asks for on a Peios machine is answered by one
process: **resolvd**, the stub resolver. It is a DNS *client* — it does
not recurse and it is not a server — and it is the only source of host
resolution, the way `authd` is the only source of identity.

## Three doors

A program reaches resolvd one of three ways, and gets the same answer
by each:

- **`getaddrinfo`** — glibc's `hosts` database is fixed to
  `libnss_peios_net.so.2`, which forwards to resolvd. There is nothing
  to configure in `nsswitch.conf` and nothing behind it: no `files`, no
  `dns`.
- **DNS on `127.0.0.53`** — for programs that resolve without libc (a
  Go binary, a musl program). `/etc/resolv.conf` is a constant file
  pointing here; it is never regenerated and carries no server list.
- **The native socket** — `/run/resolvd/resolv.sock`, for Peios tools
  and `resolv`, which get records with TTLs, where the answer came from,
  and a validation state.

A bare `printer` typed into a Go program is expanded with the same
search domains, sent to the same server and cached in the same place as
one from a C program.

## Where the servers come from

netd tells resolvd what each interface contributes — servers, search
domains, addresses, whether it carries the default route — over its
control socket, live. Nothing about that is in the registry, and
nothing is in a file. `resolv status` shows the picture:

```
hostname   workshop
netd       connected
cache      12 entries

eth0  metric 100  [default-route]
  server   10.0.2.3
  domain   lan
  subnet   10.0.2.15/24
```

A name goes to **one** interface's servers, never to all of them:

1. an *exclusive* interface, if one is up (a VPN with
   `DNSExclusive = 1` takes everything);
2. the interface whose search domain the name ends with — `git.corp`
   goes to the VPN that supplied `corp`;
3. for a reverse lookup, the interface whose subnet holds the address;
4. otherwise the interface with the default route.

That is what stops a VPN's names leaking to the coffee-shop network.
Only when *no* interface supplies servers does resolvd use
`Machine\System\Network\Resolver Servers`.

A single-label name is only ever asked with a search domain appended;
with none to apply it is simply not found, and no query leaves the
machine. A name with a dot in it is never expanded.

## Static names

There is no `/etc/hosts`. Put static names in the registry:

```
reg new Machine/System/Network/Resolver/Hosts
reg set Machine/System/Network/Resolver/Hosts printer 10.0.2.9
```

resolvd answers `printer` at every door — including the DNS door, so
the Go binary sees it too — and `10.0.2.9` reverses to `printer`. An
entry here wins over DNS. `localhost`, the machine's own hostname, and
their reverses are answered without configuration.

`.local` names are never sent to a DNS server (they belong to mDNS,
which resolvd does not yet speak), and LLMNR is never used.

## The `resolv` command

| Command | What it does |
|---|---|
| `resolv status` | Scopes, servers (with any currently demoted), cache size, counters. |
| `resolv query <name> [type]` | One question. Prints the outcome, the source (`synthetic`, `hosts`, `cache`, `dns` via which server on which interface), and the records. Exit 0 found, 2 not found, 3 unavailable. |
| `resolv lookup <name>` | The addresses of a name as `getaddrinfo` sees them, with the canonical name. |
| `resolv reverse <address>` | The names of an address. |
| `resolv flush` | Drop the cache (administrators). |

`resolv query` tells you three things `dig` cannot: whether the answer
was cached, which interface's server gave it, and — once resolvd
validates — whether it was DNSSEC-secure. Today every network answer
reports `unvalidated`.

## Not found versus unavailable

resolvd keeps two things apart that `/etc/hosts`-era stacks blur. A
name that a server says does not exist is **not found**, and is
remembered for a few minutes. A name that could not be resolved because
every server timed out or refused is **unavailable**: it is never
cached, and programs see "try again" rather than "no such host", so an
outage is not remembered as a fact.

## What is not there yet

DNSSEC validation, DNS over TLS and mDNS are not in this version;
`Resolver\Policy` is reserved for them. Per-program resolution policy
is not either — the native socket knows who is asking, so it can be
added without changing the wire.
