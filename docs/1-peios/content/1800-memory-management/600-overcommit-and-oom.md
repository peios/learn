---
title: Overcommit and OOM
type: concept
description: How Peios handles memory exhaustion — the overcommit model, the OOM killer, and the privilege gate on opting out of OOM victim selection.
related:
  - peios/memory-management/understanding-the-address-space
  - peios/memory-management/memory-mapping
  - peios/memory-management/swap
  - peios/privileges/se-tcb-privilege
---

When a system runs out of memory, something has to give. Peios inherits Linux's two-stage answer: **overcommit** lets `mmap` and friends succeed beyond the system's actual memory budget on the bet that most processes won't use everything they ask for; if the bet loses, the **OOM killer** picks a victim process and terminates it.

This page explains the model, the tunables that control overcommit policy, and the privilege gate on tampering with OOM victim selection.

## Why overcommit exists

A process that calls `malloc(1 GB)` typically does not write to all 1 GB. Allocators round up, reserve buffers in case they're needed, and request large arenas for small allocation pools. If every promised byte had to be backed by physical memory immediately, the system could support far fewer concurrent workloads than it actually can.

Overcommit lets the kernel say "fine" to the request and only allocate physical memory when the process actually touches a page. This is **demand paging** combined with **lazy commit accounting** — a pointer is returned, the VMA is recorded, but no physical page is consumed until first touch.

The trade-off: if every process eventually does touch everything it asked for, the kernel has more pages mapped into address spaces than it can back. At some moment, a page-fault arrives, the kernel goes to allocate a physical page, and there are none. Something must die.

## Overcommit policies

Three modes, controlled by a registry-driven sysctl applied via ksyncd:

| Mode | `overcommit_memory` value | Behaviour |
|---|---|---|
| Heuristic (default) | `0` | The kernel uses heuristics to allow most allocations but reject obviously-impossible ones (e.g. a single 100 TB allocation on a 32 GB box). |
| Always overcommit | `1` | Accept every allocation regardless. The "trust me" mode. |
| Strict accounting | `2` | Accept allocations only if the total commit charge stays under `(physical_RAM × overcommit_ratio / 100) + total_swap`. |

The default `0` is what most workloads expect. Mode `1` is occasionally used by HPC workloads that allocate huge sparse arrays they know they won't fully populate. Mode `2` is the **fortress** posture: no allocation can succeed if it would exceed the system's actual budget, eliminating the OOM-killer entirely at the cost of breaking software that assumes `malloc` always succeeds.

A related tunable, `overcommit_ratio`, sets the percentage of physical RAM counted toward the strict-accounting limit. The default of `50` is conservative (assuming half of RAM is reserved for kernel and caches); systems with explicit memory budgeting often set it higher.

**Image-policy implication:** desktop and developer images run in mode `0`. High-availability server images may run in mode `2` with appropriate `overcommit_ratio`, accepting the compatibility cost in exchange for predictable failure semantics. The choice is documented as part of image policy, not exposed to user processes.

## The OOM killer

When the kernel runs out of physical memory and cannot reclaim enough to satisfy a faulting allocation, it invokes the **OOM killer**. The killer scores every process and kills the one with the highest score. Killing is unconditional — the victim receives `SIGKILL` and cannot block, ignore, or recover.

The score is computed from:

- The process's RSS (resident memory) — bigger processes are bigger candidates.
- Whether the process is owned by `root`-equivalent identities (slight protection on Linux; on Peios this maps to TCB-tier processes getting some protection).
- The process's `oom_score_adj` value — see below.
- Other heuristics: child processes inherit a fraction of parent score, processes that just forked are slightly preferred targets, etc.

The killer's choice can be wrong. A small leaking process can avoid being killed if a large innocent process scores higher. This is a fundamental limitation of victim selection without per-process accounting; cgroup-based memory limits are the real solution and are documented in the **Resource Control** category.

After the kill, the **OOM reaper** asynchronously reclaims the dead process's memory without waiting for full teardown. This is important: a process that's been `SIGKILL`ed but is still running cleanup code (kernel-side) doesn't release its pages immediately. The reaper bypasses cleanup and frees the physical pages, so the system recovers quickly.

## oom_score_adj

A process's OOM score is adjusted by a per-process value, `oom_score_adj`, in the range `-1000` to `+1000`. A value of `0` is neutral; positive values make the process a more likely target; negative values make it less likely. The extreme values:

| Value | Effect |
|---|---|
| `+1000` | Always the first to die. "Sacrifice me freely." |
| `0` | Neutral. The default. |
| `-999` | Almost always spared. |
| `-1000` | Effectively immune — the killer's score arithmetic produces a non-positive result, and the kernel will not pick this process. |

A value of `-1000` is "do not kill," and it is exactly the value that creates the problem the privilege gate solves.

## The lowering privilege

A process can adjust its **own** `oom_score_adj`. Increasing it (becoming more killable) is unrestricted: any process can volunteer for sacrifice. **Decreasing** it below the current value is gated:

> Setting `oom_score_adj` to a value lower than the current value requires `SeTcbPrivilege`.

This exists because `oom_score_adj = -1000` makes the process effectively immortal under memory pressure. A misbehaving or compromised process that can pin all available RAM and refuse to die is a denial-of-service against system stability — the system thrashes indefinitely or crashes the kernel itself rather than recovering by killing the offender. The privilege gate ensures that immortality is only available to TCB-tier services that legitimately need it (peinit, supervisors of critical infrastructure).

A process started at neutral `oom_score_adj = 0` cannot lower its score without the privilege. A process inheriting `oom_score_adj = -500` from its parent can stay there and even raise the value, but it cannot drop below `-500` without the privilege. This is consistent with the general Peios principle: privileges granted at exec time are retained or relinquished, not amplified.

Setting `oom_score_adj` on **another** process follows the standard cross-process gate: `PROCESS_SET_QUOTA` (or equivalent — the access mask name will be confirmed when the process security descriptor reference is finalised) on the target's process SD plus PIP dominance. Lowering the target's value below its current also requires the caller to hold `SeTcbPrivilege`.

## panic_on_oom

For deployments where killing a process is itself an unacceptable response — typically embedded systems or appliances where the right answer to memory exhaustion is "reboot, recover from a known-good state" — the `panic_on_oom` setting causes the kernel to panic instead of invoking the OOM killer:

| Mode | Behaviour |
|---|---|
| `0` (default) | Run the OOM killer. |
| `1` | Panic, unless the OOM is constrained to a cgroup or memory policy. |
| `2` | Always panic. |

Mode `2` combined with strict overcommit (`overcommit_memory = 2`) gives a deployment with **no OOM-killer ever**: allocations either succeed at request time or fail at request time, and physical-memory exhaustion (which strict accounting prevents but cannot guarantee against bugs) reboots the system.

## Per-cgroup OOM

Memory cgroups allow setting per-group memory limits and producing OOM events scoped to a single cgroup. The `memory.oom.group` knob controls whether a cgroup-OOM kills only one victim (the highest-scoring process in the cgroup) or all processes in the cgroup. The cgroup memory model is documented fully in the **Resource Control** category; the relevant point here is that cgroup OOM and global OOM are distinct mechanisms — a cgroup OOM does not invoke the system OOM killer, and a system OOM scans all processes regardless of cgroup membership.

## Observability

`/proc/<pid>/oom_score` shows the current computed score for a process — useful for predicting who would die next. `/proc/<pid>/oom_score_adj` shows the adjustment value. Reading either is gated by `PROCESS_QUERY_INFORMATION` on the target's process SD, like other `/proc` introspection.

System-wide OOM events are logged to the audit subsystem with the victim's PID, score, RSS, and the cgroup constraint (if any). Diagnostic tools watching the audit stream see the full history of who died and why.

## See also

- [Understanding the Address Space](understanding-the-address-space) — demand paging, the substrate of overcommit.
- [Memory Mapping](memory-mapping) — `MAP_NORESERVE` opting individual mappings out of commit accounting.
- [Swap](swap) — swap as the buffer that delays the OOM trigger.
