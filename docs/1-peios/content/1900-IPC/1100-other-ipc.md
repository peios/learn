---
title: Other IPC Primitives
type: reference
description: Smaller IPC primitives on Peios — kcmp for kernel object comparison, membarrier for cross-CPU memory barriers, and cross-memory-attach syscalls.
related:
  - peios/IPC/event-fds
  - peios/memory-management/memory-mapping
  - peios/process-security/process-security-descriptors
---

A handful of IPC primitives don't fit cleanly into the larger topic pages. They're collected here for reference.

## kcmp — comparing kernel objects across processes

`kcmp(pid1, pid2, type, idx1, idx2)` compares specific kernel objects between two processes and returns whether they refer to the same underlying object. The `type` parameter selects what to compare:

| Type | Compares |
|---|---|
| `KCMP_FILE` | Two file descriptors (one per process). Returns 0 if both refer to the same open file. |
| `KCMP_VM` | Address spaces. Returns 0 if both processes share their VM (e.g. threads of the same process, or processes with `CLONE_VM`). |
| `KCMP_FILES` | fd tables. Returns 0 if both share their fd table (e.g. `CLONE_FILES`). |
| `KCMP_FS` | fs state (cwd, root). Returns 0 if both share. |
| `KCMP_SIGHAND` | Signal handler tables. |
| `KCMP_IO` | I/O contexts. |
| `KCMP_SYSVSEM` | System V semaphore undo lists. |
| `KCMP_EPOLL_TFD` | Whether one process's epoll watch list contains a target fd belonging to another process. |

Used primarily by debuggers, tracers, and CRIU (the checkpoint/restore framework) to determine whether two process references actually point at the same kernel object — important for serialising kernel state correctly.

**Access control.** `kcmp` requires `PROCESS_QUERY_INFORMATION` on **both** target processes' SDs plus PIP dominance against both. The information leaked by a positive comparison is non-trivial — knowing that two processes share their VM tells you they're threads of the same logical entity, knowing they share their fd table tells you about clone topology, etc. The query gate is appropriate.

`kcmp` is not commonly used by application code. Most users encounter it indirectly through CRIU or strace.

## membarrier — cross-CPU memory barriers

`membarrier(cmd, flags, cpu_id)` issues a memory barrier on other CPUs, ensuring memory ordering between the calling thread and threads running elsewhere. The variants:

| Command | Effect |
|---|---|
| `MEMBARRIER_CMD_GLOBAL` | System-wide barrier. Slow; affects every CPU. |
| `MEMBARRIER_CMD_GLOBAL_EXPEDITED` | IPI-based expedited barrier. Faster than `GLOBAL` but more disruptive. |
| `MEMBARRIER_CMD_PRIVATE_EXPEDITED` | Expedited barrier within the calling process only. |
| `MEMBARRIER_CMD_PRIVATE_EXPEDITED_SYNC_CORE` | Private expedited plus instruction-pipeline sync — used by JITs that have just generated new code and need other threads to discard speculative-execution state from old code at the same address. |
| `MEMBARRIER_CMD_PRIVATE_EXPEDITED_RSEQ` | Private expedited barrier for restartable-sequences (rseq) — used by lockless data structures with per-CPU operations. |
| `MEMBARRIER_CMD_REGISTER_*` | Registration variants. Some commands require explicit registration before first use, to allow the kernel to optimise. |

The motivation: traditional memory barriers (`mfence`, `dmb`) are thread-local — they enforce ordering on the executing CPU. To establish a cross-thread happens-before relationship cheaply, you'd want a barrier that ensures other threads see your prior writes before they continue. That's what `membarrier` does, by triggering each relevant CPU to execute a barrier-equivalent in a piggyback on its next quantum.

`MEMBARRIER_CMD_PRIVATE_EXPEDITED_SYNC_CORE` is the JIT case worth knowing: when a JIT compiles new code and wants to start using it, it must ensure other threads' instruction caches and pipeline state don't reflect the old code at that address. The `SYNC_CORE` variant flushes pipelines on all CPUs running the process's threads, providing the guarantee.

membarrier is unprivileged. The expedited variants require a registration call first (per-process), which is a one-time setup cost.

## Cross-memory-attach syscalls

`process_vm_readv(pid, local_iov, liovcnt, remote_iov, riovcnt, flags)` and `process_vm_writev(...)` read or write to another process's address space. These were documented in [Memory Mapping](../memory-management/memory-mapping); they're listed here only because the inventory groups them under IPC.

Access control:

- **`process_vm_readv`** requires `PROCESS_VM_READ` on the target's process SD plus PIP dominance.
- **`process_vm_writev`** requires `PROCESS_VM_WRITE` on the target's process SD plus PIP dominance.

These are the primitives debuggers and supervisors use to copy data into and out of other processes without going through ptrace. The access gates match the operations' blast radius — reading another process's memory is significant, writing to it is more so.

## See also

- [Memory mapping](../memory-management/memory-mapping) — `process_vm_readv` and `process_vm_writev` in their natural context.
- [Process security descriptors](../process-security/process-security-descriptors) — the access masks for cross-process operations.
- [Event-bearing file descriptors](event-fds) — `pidfd` operations for cross-process queries.
