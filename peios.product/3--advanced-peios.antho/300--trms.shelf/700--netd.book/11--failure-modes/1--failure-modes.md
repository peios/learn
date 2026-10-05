---
title: Failure modes
description: What goes wrong with netd, what each failure looks like from outside, where the evidence is, and how to get back to a known state.
---

## Where the evidence is

- **`net status`**: the policy refusal, each interface's verdict and the
  rule that gave it, its warning, its addresses and gateways, and its
  lease's state.
- **netd's log.** Every line goes to standard error, which peinit forwards
  to eventd (`evctl 'LOGS FROM netd SINCE 1h ago TAKE 40'`). It is also
  mirrored to `/dev/kmsg` at `KERN_INFO`, `KERN_WARNING` or `KERN_ERR`, so it
  reaches the kernel log and, at a permissive console log level, the
  console. If the mirror cannot be opened, netd says so once on standard
  error. netd opens `/dev/kmsg` once and writes every line through that
  one descriptor, and the kernel rate-limits writes per open file (by
  default ten lines in five seconds). So in a burst, the lines past the
  limit are missing from the kernel log, while eventd still has every
  one. [*failure.log-mirrored-to-kmsg]
- **The registry**: `Interfaces\<id>\Status`, `Networks\<id>\Status`,
  `Readiness`.

## No address on a joined interface

| What `net status` shows | Likely cause |
|---|---|
| `warning    asked for an address; nobody answered`, a 169.254 address or none | no DHCPv4 server answered. Either there is none, or NTFE refused the exchange: the shipped baseline's DHCP rules were deleted or overridden. netd cannot see the verdict stream. |
| no `lease` line, no warning | the profile does not offer the address (`Address.Offered`, `Address.Families`), the interface has no MAC, or the packet socket would not open (logged). Or a server is answering but its ACK does not read as a lease: no server identifier, a lease time under 4 s, or a malformed classless route option (§5.3). The client then cycles through Selecting and Requesting, neither of which is shown (§5.1). |
| no IPv6 address | no advertisement arrived, or none was accepted: hop limit under 255, a non-link-local source, a prefix that is not an autonomous /64 (§6.1, §6.2). Also check `Address.Families`. |

## The wrong interfaces are configured

| What `net status` shows | Meaning |
|---|---|
| `policy     REFUSED: …` | the newest generation was refused (§3.2). Everything shown is still the last good generation. Fix the named rule or profile; the next write is read at once. |
| `verdict    (none) by backstop` | no rule speaks for the interface. It is left as the kernel left it. |
| `verdict    (none) by <a> vs <b>`, warning `rules … tie` | two rules tied on priority and named different profiles (§3.3). The interface is ignored until one outranks the other. |
| an interface that was joined is now `IGNORE`d, with its old addresses still on it | by design: `IGNORE` touches nothing, removal included (§3.3) |

## Changes that do not stick

- **An address added by hand disappears.** netd owns every address on a
  joined interface, and the next pass removes it (§4.3). Add it to
  `Address.Static` instead.
- **A route added by hand stays,** unless it carries protocol 200.
- **A pinned gateway never appears.** `Route.Gateway` is not checked
  against the interface's subnets. When the kernel cannot reach it, every
  reconcile logs `reconcile: AddRoute(…) failed`, and the interface stays
  `addressed`.
- **The hostname does not change back** when `Hostname` is removed. netd
  never unsets a name (§8.4).

## Losing what was working

- **A cable pull drops everything offered** — the lease, autoconfigured
  addresses, routes, the network identity — and stops the clients
  (§4.1). When the carrier returns, the DHCPv4 client asks for the old
  address first, so a cooperative server restores it in one exchange.
- **A lease that cannot be renewed drops its address** at the lease's
  end, unless the profile says `Address.OnExpiry = Keep` (§5.4). After
  that, the link-local fallback does not happen again in the same
  client's life (§5.2).
- **Editing a profile restarts its interfaces' clients** (§3.3), so a
  DHCPv4 lease is released and asked for again.

## netd is slow or unresponsive

- **Everything pauses for seconds at a time.** A program that connects to
  the control socket and does not send its request holds netd's single
  loop for up to 2 s per connection (§9.1). Look for a misbehaving client
  of `/run/netd/control.sock`.
- **`net: cannot reach netd at /run/netd/control.sock`.** netd is not
  running, or `/run/netd` lost its descriptor. The service restarts
  netd always; `evctl` shows why it stopped.

## Configuration not read

- **netd ignores every registry change.** The watch could not be armed at
  startup (`registry watch unavailable … configuration is read once`), or
  `Machine\System\Network` did not exist then (§2.1). Restart netd.

## Getting back to a known state

1. Undo the last registry write. A refused generation names what to undo,
   and the next good write is taken at once.
2. `net reconcile` runs a full pass without waiting for an event.
3. `net renew <interface>` renews a lease without releasing it.
4. Restarting netd re-derives everything from the registry and the
   kernel, and restarts every client from an INIT-REBOOT (§2.1). Until a
   server answers it, a leased interface has neither its leased address
   nor its default route, and the machine's readiness falls with them,
   to `link` where nothing else is usable. A cooperative server restores
   both in one exchange.
