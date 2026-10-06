---
title: The hostname
description: Where netd's hostname comes from — the registry or a lease — when it calls sethostname, and what it does not do.
---

## Which name [*hostname.source]

1. `Machine\System\Network Hostname`, when it is set and not empty;
2. otherwise the hostname option (12) of a lease. netd takes the first
   joined interface, in kernel index order, whose profile has
   `Hostname.Offered` and whose lease carries a hostname;
3. otherwise none.

The name is passed to the kernel as written. netd does not check the
registry value against the one-label rule (`libnetd::hostname`, which
System Settings and first-boot setup apply before writing it), and it
does not check a lease's name at all. A name the kernel refuses, such as
one longer than 64 bytes, is logged as `sethostname(<name>): <error>`
and tried again at the next pass. [*hostname.passed-as-written]

## When [*hostname.applied-after-each-pass]

After every full pass and every reconcile-only iteration (§2.2), netd
calls `sethostname(2)` if the name differs from the last one **it** set,
and logs `hostname is <name>`. It does not compare against the kernel's
current hostname. A change made by anything else is not reverted until
netd's own name changes.

When there is no name — the registry value removed and no lease offering
one — netd does nothing: the kernel keeps whatever hostname it had.
[*hostname.never-unset]

The status reply and the resolver snapshot report the name netd last
set, empty if it has set none.

## What is recorded

Each `sethostname(2)` that changes the kernel's name writes a
`netd.hostname.changed` event, which is `essential`: the emission policy
cannot switch it off. It carries `config.name` (always `Hostname`, whether
the name came from the registry or from a lease), `config.text` (the name
now in force) and `config.text-previous` (the kernel's name, read just
before the call; the kernel's own `(none)` on the first change after boot).
A call that leaves the kernel's name as it was — netd setting a name the
kernel already holds, as after a restart of netd or a change made behind
its back — records nothing, and neither does a name the kernel refuses.
[*hostname.change-recorded]

The record's `subject.token.sid` is the principal that acted (PGSS §6.4).
When the change is made during the pass a `reconcile` request (§9.2) asked
for, that is the requester's user SID; netd refuses a request whose user
it cannot read. A change netd makes on its own authority — after a
registry change, a lease, or at startup — names netd's own user, SYSTEM;
who wrote the registry value is LCS's to record.
[*hostname.requester-recorded]

## Telling the network

With `Hostname.Announce` in an interface's profile, its DHCPv4 client sends
the registry's `Hostname` in option 12 (§5.1). A name adopted from a
lease is never announced.
