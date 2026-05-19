---
title: Enforcement Points
---

PIP process isolation is enforced at kernel hook sites. Each hook reads `pip_type` and `pip_trust` from the caller's PSB and the target's PSB, performs the dominance check, and denies the operation if the caller does not dominate.

## SeDebugPrivilege and process SD interaction

All process-to-process operations perform two checks: (1) an AccessCheck against the target's process SD, and (2) a PIP dominance check. SeDebugPrivilege bypasses only the process SD check — it MUST NOT bypass PIP dominance. This applies uniformly to all enforcement points: ptrace, signal delivery, prlimit, process information query/set, token open operations, and target-specific performance monitoring.

## ptrace

ptrace grants full control over the target: read/write memory, read/write registers, single-step execution, inject signals, modify execution flow. A single successful ptrace attach is equivalent to full compromise of the target process.

If the caller does not dominate the target, the operation MUST be denied regardless of ptrace mode. SeDebugPrivilege bypasses the process SD check but MUST NOT bypass PIP dominance.

For process-SD purposes, ptrace mode maps as follows:

- `PTRACE_MODE_READ*` requires `PROCESS_VM_READ`.
- `PTRACE_MODE_ATTACH*` requires `PROCESS_VM_WRITE`.

`PTRACE_TRACEME` nominates another process as the tracer and therefore uses
the nominated tracer as the subject and the calling process as the target. It
MUST require `PROCESS_VM_WRITE` on the target process SD plus PIP dominance.
SeDebugPrivilege bypasses only the target process-SD check and MUST NOT
bypass PIP.

## pidfd_open

`pidfd_open()` acquires a stable handle to an existing process. It is a
process-boundary information query, not a memory-access or debugger-attach
operation.

`pidfd_open()` requires `PROCESS_QUERY_LIMITED` on the target process's SD,
plus PIP dominance. `SeDebugPrivilege` bypasses only the SD check and MUST NOT
bypass PIP.

## Process memory access

Direct memory access (`/proc/pid/mem`, `process_vm_readv`, `process_vm_writev`) goes through the same ptrace access check in the kernel. The PIP check in the ptrace hook covers all memory access vectors.

> [!INFORMATIVE]
> This is critical for secret-keeping processes. An HSM daemon's in-memory key material is protected by the kernel refusing to let any non-dominant process read its address space. The secret genuinely cannot leak to a compromised administrator.

## Signal delivery

Signals can disrupt, terminate, or debug a process. If the caller does not dominate the target, signal delivery MUST be denied. PIP dominance is checked uniformly regardless of signal type.

The process SD provides per-signal granularity via three access rights: PROCESS_TERMINATE (lethal signals), PROCESS_SUSPEND_RESUME (stop/continue signals), and PROCESS_SIGNAL (informational signals). See §5.3 for the full mapping.

Userspace signal probes with signal `0` do not deliver a signal, but they do
query process existence and permission. They require `PROCESS_QUERY_LIMITED`
on the target process SD plus PIP dominance.

This means lifecycle management of PIP-protected processes (shutdown, restart) MUST go through a process that dominates them — in practice, peinit, which runs at the highest trust level.

## /proc metadata

`/proc/pid/` exposes process metadata: command line, memory maps, open file
descriptors, environment, status, scheduler state, namespace state, timer
state, and mitigation/debug state. Some entries are already ptrace-gated or
memory-open-gated (`mem`, `maps`, `smaps`, `smaps_rollup`, `pagemap`,
`numa_maps`, `map_files`, `fd`, `fdinfo`, `environ`, `auxv`, and similar
memory or fd inspection paths) — the PIP ptrace hook covers these automatically.

For PIP-protected processes, non-ptrace-gated proc metadata leaks process
information. PIP MUST enforce visibility on those entries: if the caller does
not dominate the target and the target is PIP-protected, access MUST be
denied.

For process-SD purposes, read-only proc metadata maps as follows:

- Basic process metadata requires `PROCESS_QUERY_LIMITED`: `stat`, `statm`,
  `comm`, `wchan`, `schedstat`, `cpuset`, `cgroup`,
  `cpu_resctrl_groups`, `oom_score`, `sessionid`, `patch_state`,
  `stack_depth`, and `arch_status`.
- Detailed process metadata requires `PROCESS_QUERY_INFORMATION`: `cmdline`,
  `status`, `io`, `limits`, `sched`, `autogroup`, `timens_offsets`,
  `personality`, `syscall`, `latency`, `timers`, `timerslack_ns`,
  `mounts`, `mountinfo`, `mountstats`, `coredump_filter`, `oom_adj`,
  `oom_score_adj`, `loginuid`, `make-it-fail`, `fail-nth`, `seccomp_cache`,
  `ksm_merging_pages`, and `ksm_stat`.

Entries that are native-debug-only or otherwise stricter than these metadata
queries, such as `/proc/<pid>/stack`, continue to be governed by their native
hardening plus the KACS ptrace/process checks on that path.

Writable proc knobs are separately classified as mutation paths. This metadata
rule covers the read side; it is not permission to mutate scheduler,
namespace, OOM, fault-injection, timer, memory-accounting, or dumpability
state.

For process-SD purposes, procfs process mutation paths map as follows:

- Writes to `sched`, `autogroup`, `timens_offsets`, `timerslack_ns`,
  `coredump_filter`, `oom_adj`, `oom_score_adj`, `make-it-fail`, `fail-nth`,
  `latency`, and `clear_refs` require `PROCESS_SET_INFORMATION` on the target
  process SD plus PIP dominance.
- `uid_map`, `gid_map`, `projid_map`, and `setgroups` are open-time seq files
  whose read and write file modes are coupled. Opening them with read intent
  requires `PROCESS_QUERY_INFORMATION`; opening them with write intent requires
  `PROCESS_SET_INFORMATION`. Opening with both read and write intent requires
  both checks to pass.
- OOM adjustment writes can fan out to other Linux processes sharing the same
  mm. Until KACS implements complete multi-target authorization for that
  fan-out, the operation MUST fail closed when Linux detects that the target
  has a multiprocess mm.

Same-process-only compatibility writes, such as `comm` and `loginuid`, remain
under their native same-process restrictions and do not cross the process
security-state boundary.

> [!INFORMATIVE]
> Denying access prevents reading files within `/proc/pid/` but does not hide the PID from directory listings. The PID and directory name remain visible via `getdents`. Full invisibility would require additional hook coverage. For v0.20, visible-but-inaccessible is acceptable.

> [!INFORMATIVE]
> `/proc` is not FACS-managed — it is a virtual filesystem with no backing
> store and no xattrs. Process access there is still controlled by the target
> process's SD plus PIP dominance, but the enforcement happens through direct
> kernel checks rather than through an object-backed FACS AccessCheck path.

## Capability metadata (`capget` and `/proc/<pid>/status`)

`capget()` exposes Linux compatibility capability state. When the caller
targets the current process, or another thread sharing the same process
security state, the process-boundary checks do not apply.

`capget(pid)` targeting another process is a detailed process information
query. It requires `PROCESS_QUERY_INFORMATION` on the target process's SD,
plus PIP dominance. `SeDebugPrivilege` bypasses only the process-SD check and
MUST NOT bypass PIP.

`/proc/<pid>/status` also exposes Linux compatibility capability state through
the `CapInh`, `CapPrm`, `CapEff`, `CapBnd`, and `CapAmb` fields. Access to
the status file is governed by the `/proc` metadata rule above.

## Resource limits (prlimit)

Read-only `prlimit` operations require `PROCESS_QUERY_INFORMATION` on the
target's process SD, plus PIP dominance. `prlimit` operations that change a
limit require `PROCESS_SET_INFORMATION` on the target's process SD, plus PIP
dominance. SeDebugPrivilege bypasses the SD check but not PIP.

Self-directed scheduler and resource-limit changes are not process-boundary
operations. When the target is the calling process itself, the process-SD and
PIP process-boundary checks do not apply.

## Process attribute tail

Linux exposes additional process attribute hooks for process group/session,
scheduler, affinity, I/O priority, and memory-placement operations. KACS maps
them as follows when the target belongs to a different process security state:

- `setpgid()` requires `PROCESS_SET_INFORMATION` on the target process SD,
  plus PIP dominance.
- `getpgid()` and `getsid()` require `PROCESS_QUERY_LIMITED` on the target
  process SD, plus PIP dominance.
- `sched_getscheduler()`, `sched_getparam()`, `sched_getattr()`,
  `sched_getaffinity()`, `sched_rr_get_interval()`, `/proc/<pid>/timerslack_ns`
  reads, and `ioprio_get()` require `PROCESS_QUERY_INFORMATION` on the target
  process SD, plus PIP dominance.
- target memory-placement mutations covered by Linux's `task_movememory` hook
  require `PROCESS_SET_INFORMATION` on the target process SD, plus PIP
  dominance.

Same-process and same-process-security-state operations are not
process-boundary operations and bypass this gate. SeDebugPrivilege bypasses
only the process-SD check and MUST NOT bypass PIP dominance.

## CPU affinity (`sched_setaffinity`)

CPU affinity is per-thread, but changing the affinity of the calling thread or
another thread in the same process is not a process-boundary operation. In that
same-process case, the process-SD and PIP process-boundary checks do not apply.

Changing the affinity of a thread in a different process requires
`PROCESS_SET_INFORMATION` on the target process's SD, plus PIP dominance, plus
`SeIncreaseBasePriorityPrivilege`. `SeDebugPrivilege` bypasses only the
process-SD check and MUST NOT bypass either PIP or
`SeIncreaseBasePriorityPrivilege`.

KACS does not relax the kernel's native affinity validity rules. If the
requested mask is invalid or outside the kernel's currently allowed set for the
target thread, the call still fails regardless of privilege or SD state.

## Token open operations

Opening another process's primary token (`kacs_open_process_token`) or a thread's token (`kacs_open_thread_token`) requires PROCESS_QUERY_INFORMATION on the target's process SD, plus PIP dominance. These are process-boundary-crossing operations — reading a process's security identity is as sensitive as reading its memory.

## Performance monitoring (perf_event_open)

`perf_event_open()` targeting a specific process can leak execution timing,
branch prediction behavior, cache access patterns, and instruction traces.
Those side channels can reveal cryptographic keys and other protected process
secrets.

Target-specific `perf_event_open()` requires
`SeProfileSingleProcessPrivilege`. Cross-process target-specific monitoring
also requires `PROCESS_QUERY_INFORMATION` on the target process's SD, plus PIP
dominance. `SeDebugPrivilege` bypasses only the process-SD check and MUST NOT
bypass PIP or the standalone profile privilege.

Self-directed perf monitoring and perf monitoring of another thread in the
same process are not process-boundary operations. In that same-process case,
the process-SD and PIP process-boundary checks do not apply, but
`SeProfileSingleProcessPrivilege` is still required.

CPU-wide perf and cgroup perf modes are not target-specific process operations
under this rule. They remain governed by Linux's native perf permission model
in `v0.20`.

## /dev/mem and /dev/kmem

`/dev/mem` provides raw access to physical memory. A process with access to `/dev/mem` could read any process's memory by mapping its physical pages, bypassing all virtual memory protections including PIP.

The primary defense is `CONFIG_STRICT_DEVMEM=y`, which restricts `/dev/mem` to I/O regions only (no RAM access). This is a kernel build configuration requirement. As a secondary defense, FACS SHOULD place a restrictive SD on `/dev/mem` and `/dev/kmem`.
