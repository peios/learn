---
title: Debugging the kernel
type: concept
description: The PKM subsystems — KACS, KMES, LCS — expose static tracepoints to the standard Linux tracing stack of ftrace, perf, and eBPF.
related:
  - peios/debugging-the-kernel/kernel-tracepoints
  - peios/access-decisions/debugging-a-denial
  - peios/inspecting/overview
  - peios/kernel-abi-reference/overview
---

Most questions about *why* the Peios kernel did something — why an access was denied, why an event never reached userspace, why a registry lookup stalled — are answered from inside the kernel, before any userspace tool can see the state involved. Peios makes that interior observable through the same tracing infrastructure the rest of the Linux kernel uses: **static tracepoints**.

The PKM security subsystems each expose a tracepoint system:

- **`kacs:`** — the access-control decisions. Every instrumented KACS hook records its verdict (allow/deny), the object it acted on (inode number and superblock magic — never a pathname), and a `reason` code naming the exact return path it took. This is where "why was this denied?" is answered.
- **`kmes:`** — the health of the event substrate: ring-buffer drops, capacity swaps, rate-limit throttling, backpressure. These trace the *machinery*, not the security events KMES ships to userspace (those are the [event stream](~peios/inspecting/the-event-stream)).
- **`lcs:`** — the registry source device: request/response round-trips, timeouts, transaction state transitions, source mark-downs.

Because these are ordinary kernel tracepoints, everything the kernel's tracing stack can do applies unchanged: enable individual events or whole subsystems, attach ftrace filters and triggers, sample with perf, or attach eBPF programs. They cost nothing when disabled (a patched-out branch) and record structured fields rather than formatted text, so you filter on `ret`, `reason`, or an inode number directly.

The [Kernel tracepoints](~peios/debugging-the-kernel/kernel-tracepoints) page covers how to enable them — at runtime through `tracefs`, or from the very first moments of boot through the kernel command line — and how to read what they emit.

> [!NOTE]
> **Safety.** PKM tracepoints never record pathnames or security-descriptor bytes. They carry inode numbers, superblock magics, resolved policies, access masks, numeric identifiers, lengths, and reason codes only. This is by design, so they are safe to leave compiled into production kernels and enable in the field.
