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

## Telling the network

With `Hostname.Announce` in an interface's profile, its DHCPv4 client sends
the registry's `Hostname` in option 12 (§5.1). A name adopted from a
lease is never announced.
