---
title: "kernel.*"
description: "Every field the evman catalogue defines under kernel: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `kernel`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="kernel.build.disabled"></a>`kernel.build.disabled`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The security-relevant kernel build options this kernel was built without,
by `CONFIG_` name. They matter as much as those enabled: an option that
should be off — a second packet-filtering framework, a mandatory access
control module Peios does not use — would be a second, unratified policy
surface, and a kernel built with it on is otherwise indistinguishable
from one built correctly.

**Carried by:**

No event carries this field yet.

## <a id="kernel.build.enabled"></a>`kernel.build.enabled`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The security-relevant kernel build options this kernel was built with,
by `CONFIG_` name, such as `CONFIG_MODULE_SIG_FORCE` and
`CONFIG_STRICT_DEVMEM`. Only the options that bear on security are
listed, not the whole configuration.

**Carried by:**

No event carries this field yet.

## <a id="kernel.divergence.checks"></a>`kernel.divergence.checks`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The checks stock Linux makes that this kernel does not, one name per
check. Peios removes or replaces several upstream checks — the
capability-based ptrace gate, the credential tests in signal delivery,
the switch to real credentials in `faccessat` — because KACS makes those
decisions instead. An investigator reasoning from Linux semantics will be
wrong about each one, and this is where to find out which. Nothing emits
the field yet, so the names it will carry are not yet fixed.

**Carried by:**

No event carries this field yet.

## <a id="kernel.divergence.reports"></a>`kernel.divergence.reports`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The values this kernel reports differently from stock Linux, one name per
divergence. Where `kernel.divergence.checks` lists checks not made, this
lists answers that differ: `getuid` and `getgid` reading the task's real
credentials, `SO_PEERCRED` and the filesystem identity carrying the IDs
KACS projects, the capability sets in `/proc` and from `capget`
rewritten. **Correlating Linux uids across sources fails silently without
it**, because a peer credential and a `/proc` entry can disagree in ways
stock Linux never produces. Nothing emits the field yet, so the names it
will carry are not yet fixed.

**Carried by:**

No event carries this field yet.

## <a id="kernel.lockdown"></a>`kernel.lockdown`

- **Type:** `str.enum`
- **Values:** `none` · `integrity` · `confidentiality`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The kernel lockdown level in force. A Peios kernel is built to force
`integrity`, which refuses the paths that write to the running kernel —
`/dev/mem`, `kexec`, hibernation, raw MSR writes, unsigned BPF — to every
principal however privileged; KACS has no say in it and no privilege lifts
it. Any other value means the machine is not running a kernel built as
Peios builds it.

**Carried by:**

No event carries this field yet.

## <a id="kernel.lsms"></a>`kernel.lsms`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The Linux security modules active, in the order the kernel calls them; a
Peios kernel runs `landlock`, `lockdown`, `integrity` and `pkm`. The list
is fixed and checked when the kernel is built but stated nowhere at
runtime, so without this field a machine booted on a kernel built some
other way cannot be told apart from one that was not.

**Carried by:**

No event carries this field yet.

## <a id="kernel.securityfs-node"></a>`kernel.securityfs-node`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The securityfs node an initialisation concerned, as its path beneath the
securityfs root (`/sys/kernel/security`), such as `kacs/sessions`. A node
that fails to be created makes every tool that reads it fail with
`ENOENT`, and this is where the cause is recorded. KACS creates its nodes
all or nothing, so one failure leaves the whole `kacs` directory absent.

**Carried by:**

No event carries this field yet.

## <a id="kernel.version"></a>`kernel.version`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The Linux kernel release actually running, as `uname -r` reports it.
Peios pins the upstream version it builds on and checks it at build time,
but nothing else states it at runtime.

**Carried by:**

No event carries this field yet.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
