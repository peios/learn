---
title: The Boot Attempt Counter
description: The on-disk counter that turns a repeated failure into an escalation — its cycle, and the threshold that reaches Recovery.
---

The counter is what turns a repeated failure into an escalation. peinit
keeps it at `/.peinit/boot-attempts`, as a plain decimal integer in a
file on the root filesystem — deliberately not in the registry, because
the registry may be the reason the boot is failing.

## The cycle

peinit reads the counter at startup, before selecting a boot mode. The
recovery threshold is evaluated against this **pre-increment** value, so
a default threshold of 3 admits exactly three boot attempts before
recovery.

- **Absent file:** treated as 0.
- **Unreadable, empty, non-decimal, carrying trailing non-whitespace
  data, or overflowing the counter representation:** recovery. A counter
  that cannot be read cannot be trusted to escalate.

peinit increments once per boot, after the root is known writable and
before Phase 2 begins. Incrementing before the root is known writable
would silently lose the increment on a read-only root and defeat
escalation entirely.

The increment happens after the mount, seed, machine ID and clock steps
rather than immediately after the writability probe, because reading the
kernel command line requires `/proc`. One consequence is that a recovery
entered from a mount failure, a machine ID failure, or an unreadable
command line does not advance the counter.

A write failure — a full disk, say — is treated as a counter of 0 and
the boot continues. A failure to record an attempt is not itself a
reason to escalate.

The counter resets to 0 on a successful Full or Safe boot, after the
grace period.

## Recovery threshold

The threshold is `peios.bootattempts=N` on the kernel command line,
defaulting to 3. It is a command-line value rather than a registry one
because the check runs in Phase 1, before registryd is serving.

`peios.bootattempts=0` disables the check entirely — the escape hatch
for a system whose counter is itself the fault.

`peios.recovery=1` forces recovery without consulting the counter, but
does not suppress the increment.

> [!NOTE]
> The counter catches boots where peinit runs but the system never
> reaches health — a crash-looping Critical service being the usual
> case. It deliberately does not try to catch a peinit too broken to
> reach its own increment. Recovery mode is itself a peinit mode, so a
> peinit that cannot start cannot deliver recovery either, and a higher
> count could not help. That failure belongs to binary integrity, not to
> the counter.
