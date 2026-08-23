---
title: Boot Modes
description: Full, Safe and Recovery — the escalation path from normal operation to last-resort maintenance, and what causes each downgrade.
---

peinit boots in one of three modes, forming an escalation path from
normal operation to last-resort maintenance.

```
Full boot ---+-- success ----------------> counter reset, operational
             |
             +-- cycle w/ Critical ------> Safe mode (no reboot)
             |
             +-- conflict w/ Critical ---> Safe mode (no reboot)
             |
             +-- Critical failure -------> sync + reboot --+
                                                           |
Safe boot ---+-- success ----------------> counter reset,  |
             |   operational (reduced)                     |
             +-- Critical failure -------> sync + reboot --+
                                                           |
                             counter increments <----------+
                                        |
                             counter >= N ---------> Recovery mode
                             Phase 1 failure ------> Recovery mode
```

## Full mode

The default. Every boot-triggered service starts in dependency order, as
§2.5 describes.

## Safe mode

Safe mode starts a reduced set. Eligibility is a filter *within* the
boot-triggered set, not a replacement for it: a service with no `boot`
trigger does not auto-start in Safe mode whatever its `SafeMode` or
`ErrorControl` says, and remains demand-only. Within the boot-triggered
set, two categories are eligible:

- **Critical services** (`ErrorControl=Critical`) start. If one fails,
  the ordinary Critical failure path applies — restart budget, reboot,
  counter increment, eventually recovery.
- **`SafeMode=1` services** are attempted best-effort. If one fails,
  Safe mode continues without it.

`ErrorControl=Critical` implies `SafeMode`, so a Critical service does
not have to declare both.

### What caused the downgrade

The rebuild discards the Full-mode graph, so the services that forced
Safe mode are never entered into the blocked set and are never marked
Failed. That is deliberate: Safe mode was never going to start them, and
a Failed state would say something about their own health that is not
true. `status` should keep meaning "this service is broken".

The reason is therefore recorded at **boot level** rather than per
service. Every finding that forced the downgrade — each critical cycle,
each critical boot conflict — is written to the console and emitted as a
`boot.safe_mode_downgrade` KMES event naming the services involved.

All of them are reported, not just the first. A machine can be downgraded
by a cycle *and* a conflict at once, and an operator who fixed only the
one they were shown would reboot straight back into Safe mode.

peinit rebuilds the dependency graph from scratch using only the
eligible services. Dependencies on excluded services are dropped: if A
depends on non-Critical B and B is excluded, A's dependency on B does
not exist in the Safe mode graph. This is what makes Safe mode useful —
it is a graph in which the broken parts of the configuration are simply
not present, rather than a graph in which they are present and failing.

A successful Safe boot resets the boot attempt counter.

> [!NOTE]
> Safe mode is purely a boot-sequencing concern. Once booted, an
> administrator starts anything by hand exactly as in Full mode. It is
> for a system whose configuration is broken but whose TCB is healthy.

### Entry

- **A cycle involving a Critical service at boot.** Graph validation
  detects it and peinit downgrades in place, without rebooting — the
  cycle is a configuration error, and rebooting would find it again.
- **An unresolvable conflict involving a Critical service at boot.**
  Same reasoning.
- **`peios.safemode=1`** on the kernel command line.

Safe mode is not entered because a Critical service crashed at runtime.
That follows the ordinary path: restart budget, reboot, counter
increment, recovery.

## Console output

`peios.quiet=N` bounds what peinit writes to the console:

| Value | Behaviour |
|---|---|
| `0` | Write unconditionally. |
| `1` | Do not write to a terminal held as the controlling terminal of a running service, except to announce loss of the system. This is the default. |
| `2` | Additionally drop ordinary progress everywhere, while still emitting errors. |

The two rules are independent, and an error is never less visible at `2`
than at `1`. A terminal is matched by device rather than by path, since
`/dev/console` and `/dev/ttyS<n>` can name the same device; where the
device cannot be determined, peinit falls back conservatively and treats
the terminal as held. Suppressed messages are discarded rather than
buffered.

The autorun step (§2.3) bypasses the policy: a script that ran that
early and went wrong is worth interrupting a login prompt for.

## Kernel command line

| Parameter | Effect |
|---|---|
| `peios.safemode=1` | Force Safe mode. |
| `peios.recovery=1` | Force recovery mode regardless of the counter. |
| `peios.bootattempts=N` | Set the recovery threshold; `0` disables the check. |
| `peios.quiet=N` | Console verbosity, as above. |
| `peios.notifysocket=PATH` | Override the notification socket path. |

A malformed value is ignored in favour of the default rather than
failing the boot. Nothing exists this early to report a diagnostic to.
