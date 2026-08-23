---
title: Kernel tracepoints
type: how-to
description: "Enabling and reading the kacs:, kmes:, and lcs: tracepoint systems — at runtime through tracefs, at boot through the kernel command line."
related:
  - peios/debugging-the-kernel/overview
  - peios/access-decisions/debugging-a-denial
  - peios/kernel-abi-reference/overview
---

PKM exposes its security subsystems through three tracepoint systems — `kacs:`, `kmes:`, and `lcs:` — registered with the standard Linux tracing infrastructure. This page shows how to turn them on and read them.

## Discovering the events

Every event and its fields are self-describing through `tracefs`. The live catalog is authoritative — prefer it over any static list:

```sh
# every PKM tracepoint
ls /sys/kernel/tracing/events/kacs /sys/kernel/tracing/events/kmes /sys/kernel/tracing/events/lcs

# the fields (and their symbolic decodings) of one event
cat /sys/kernel/tracing/events/kacs/kacs_file_access/format
```

The numeric `reason`, `op`, and `state` codes carried by these events are a stable, append-only diagnostic ABI defined in `<pkm/trace.h>`; the `format` file maps them back to their symbolic names for you.

## Enabling at runtime

Enable a whole subsystem, or a single event:

```sh
cd /sys/kernel/tracing

echo 1 > events/kacs/enable                 # all KACS access-decision events
echo 1 > events/kacs/kacs_file_access/enable # just one

cat trace                                    # read what has accumulated
echo 1 > tracing_on                          # (on by default)
```

Because the fields are structured, you filter in the kernel rather than grepping text. To see only **denials**:

```sh
echo 'ret != 0' > events/kacs/kacs_file_access/filter
```

To watch a single inode, or one `reason`:

```sh
echo 'ino == 1234' > events/kacs/kacs_file_access/filter
echo 'reason == 3' > events/kacs/kacs_sd_cache_lookup/filter   # 3 == miss-needs-synth
```

perf and eBPF attach to the same tracepoints by name — e.g. `perf record -e kacs:kacs_file_access`, or a `tracepoint:kacs:kacs_file_access` probe from `bpftrace`.

## Enabling at boot

The most common reason to reach for these is a decision that happens *before userspace exists* — the access checks that fire as the root filesystem mounts. `tracefs` is not available that early, so enable the events on the kernel command line and route them to the console with `tp_printk`:

```
trace_event=kacs:*,kmes:*,lcs:* tp_printk
```

`trace_event=` enables the listed events as the tracing subsystem initialises — which happens before the PKM LSM itself initialises, and well before the first access check — so no early decision is missed. `tp_printk` prints each enabled tracepoint to the kernel log, giving you a complete decision transcript on the console with no userspace involved. Narrow the selection (`trace_event=kacs:kacs_file_access`) to cut the volume.

> [!NOTE]
> **Migration note.** This replaces the older `kacs.trace=1` boot parameter, which emitted a single hand-rolled `pr_info` line per KACS access decision. The equivalent today is `trace_event=kacs:* tp_printk`, which produces the same pre-userspace transcript but as structured, filterable events across all three subsystems. `kacs.trace=1` is no longer recognised.

## Reading a KACS access decision

A `kacs:` access-decision event answers "what did KACS decide about this object, and why?". The key fields:

- **`verdict`** — `allow` or `deny`, derived from `ret` (`0` is allow; a negative errno is a denial). Filter on `ret` for machine use.
- **`reason`** — the specific return path taken, as a symbolic name (e.g. `decision`, `unmanaged`, `no-token`, `pip-context`). The same object can be denied for very different reasons; this names which one.
- **`ino` / `sb_magic`** — the inode number and the filesystem's superblock magic, identifying the object without disclosing its path.
- **`mount_policy`** — the resolved [mount policy](~peios/mount-policies/overview) for the object's filesystem, which frequently explains a denial on an unmanaged or synthesis-only mount.
- **`access`** — the desired-access mask being checked.

For a worked example of tracing a specific denial end to end, see [Debugging a denial](~peios/access-decisions/debugging-a-denial).
