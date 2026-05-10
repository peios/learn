---
title: ptrace
type: concept
description: The ptrace debugger interface — self-trace, cross-process attach, the layered model (PIP + PtraceScope + SeDebugPrivilege + target SD), sub-operations, and PIP compliance.
related:
  - peios/tracing/overview-and-design
  - peios/tracing/instrumentation-primitives
  - peios/tracing/privileges-and-controls
  - peios/privileges/debug
  - peios/pip/overview
---

`ptrace()` is the original Unix process tracer. It is a **bidirectional control protocol**, not an observability pipe — the tracer can pause the tracee, read and write its memory and registers, restart and skip syscalls, single-step, install breakpoints, and inject signals. Used by debuggers (gdb, lldb), `strace`, `ltrace`, sandbox runtimes, and emulator stacks (Wine via `PTRACE_SET_SYSCALL_USER_DISPATCH`).

ptrace is the well-behaved primitive in this section — it has an explicit attach moment per (tracer, tracee) pair, so PIP dominance is a question with an answer at that moment. This stands in contrast to kprobes/uprobes, which have no per-target attach and therefore cannot enforce PIP per-trap.

## The syscall

```c
long ptrace(enum __ptrace_request request, pid_t pid,
            void *addr, void *data);
```

Many operations multiplexed through the `request` parameter. The major ones:

### Attach and detach

| Request | Effect |
|---|---|
| `PTRACE_TRACEME` | Self: "let my parent trace me." Issued by the tracee. |
| `PTRACE_ATTACH` | Tracer attaches to a target PID. Sends `SIGSTOP`. Legacy. |
| `PTRACE_SEIZE` | Modern attach. Does not send a signal; tracee continues running until explicitly stopped. |
| `PTRACE_DETACH` | Release a tracee. |
| `PTRACE_INTERRUPT` | Stop a `SEIZE`d tracee. |
| `PTRACE_LISTEN` | Restart a tracee in a stopped state, waiting for the next event without resuming execution. |

### Memory access

| Request | Effect |
|---|---|
| `PTRACE_PEEKTEXT` / `PEEKDATA` | Read a word from tracee's memory. |
| `PTRACE_PEEKUSER` | Read a word from tracee's user-area struct (registers, debug state). |
| `PTRACE_POKETEXT` / `POKEDATA` | Write a word to tracee's memory. |
| `PTRACE_POKEUSER` | Write a word to tracee's user-area struct. |

### Register access

| Request | Effect |
|---|---|
| `PTRACE_GETREGS` / `SETREGS` | Read/write tracee's general-purpose registers. Architecture-specific. |
| `PTRACE_GETREGSET` / `SETREGSET` | Read/write a named register set (NT_PRSTATUS, NT_FPREGSET, NT_X86_XSTATE, etc.). The modern, register-set-aware version. |

### Syscall control

| Request | Effect |
|---|---|
| `PTRACE_SYSCALL` | Restart and stop at the next syscall entry or exit. The mechanism behind `strace`. |
| `PTRACE_SYSEMU` | Restart and stop before syscall entry, but skip kernel execution of the syscall. The tracer can emulate it. |
| `PTRACE_GET_SYSCALL_INFO` (5.3+) | Structured syscall info — arguments, return value, which transition (entry/exit/seccomp). |
| `PTRACE_SECCOMP_GET_FILTER` | Read the active seccomp filter from a tracee. **Additional privilege required.** |
| `PTRACE_SET_SYSCALL_USER_DISPATCH` (5.11+) | Configure the tracee to handle some syscalls in userspace via the user-dispatch mechanism. Used by Wine and other emulators. |

### Auto-attach options

`PTRACE_SETOPTIONS` accepts a bitmask of `PTRACE_O_*` flags that configure automatic behaviour:

| Option | Effect |
|---|---|
| `PTRACE_O_TRACESYSGOOD` | Mark syscall stops with bit 7 set in the signal number, so tracer can distinguish them from real `SIGTRAP`. |
| `PTRACE_O_TRACECLONE` / `TRACEFORK` / `TRACEVFORK` | Auto-attach to children spawned via clone/fork/vfork. |
| `PTRACE_O_TRACEEXEC` | Stop on `execve` and notify the tracer. |
| `PTRACE_O_TRACEEXIT` | Stop just before tracee exits. |
| `PTRACE_O_TRACESECCOMP` | Notify the tracer when seccomp triggers a `SECCOMP_RET_TRACE` action. |

## The layered access-control model

Cross-process ptrace on Peios is gated by four layers, **all of which must pass**:

1. **PIP dominance** — the tracer's integrity must dominate the tracee's. This is mandatory and has no userspace bypass. Even `SeDebugPrivilege` does not override PIP.
2. **`PtraceScope` registry knob** — provides default scoping per system-wide policy. See below.
3. **`SeDebugPrivilege`** — a holder may override `PtraceScope` (but not PIP).
4. **Target SD** — the tracee's process security descriptor. `PROCESS_VM_READ` and `PROCESS_VM_WRITE` rights gate ptrace-class authority. The target may grant or deny ptrace access independently of the other layers.

Self-trace via `PTRACE_TRACEME` bypasses these checks — a process can always self-trace.

### `PtraceScope`

The `\System\Tracing\PtraceScope` registry knob, integer 0–3, sets the default cross-process scope:

| Value | Cross-process ptrace allowed for |
|---|---|
| `0` | Same-principal cross-process allowed, plus descendants. |
| `1` | Descendants only (parent → child / grandchild / ...). **Default.** |
| `2` | `SeDebugPrivilege` required for any cross-process. |
| `3` | Disabled — no cross-process ptrace. |

The default `1` matches modern Linux distros' Yama default. Same-principal free-for-all is a real malware foothold (a process running as your principal can dump your browser's saved credentials, ssh-agent state, etc.), so descendants-only is the right starting point.

The `\System\Tracing\PtraceEnabled` knob (default `true`) is the master kill switch.

### `SeDebugPrivilege`

`SeDebugPrivilege` overrides `PtraceScope` — a holder can attach to processes outside descendant relationships and outside their own principal scope. It does **not** override PIP — a `SeDebugPrivilege` holder cannot debug a process whose integrity dominates theirs.

This is what makes ptrace fully PIP-compliant: every cross-process operation lands on a PIP check that no privilege except `SeLoadDriverPrivilege` can bypass, and `SeLoadDriverPrivilege` does not ptrace.

### Target SD

The tracee's process SD carries `PROCESS_VM_READ` and `PROCESS_VM_WRITE` rights. A target may grant these to specific principals (allowing ptrace from those principals without `SeDebugPrivilege` and outside descendant scope), or deny them (preventing ptrace from principals that would otherwise be allowed by `PtraceScope`).

Default process SDs grant `PROCESS_VM_READ` / `PROCESS_VM_WRITE` to the process's own principal — which is what makes the descendant-trace and same-principal cases work.

## PIP compliance — the structural picture

Every path through ptrace lands on a PIP check:

| Operation | Where PIP is checked |
|---|---|
| `PTRACE_TRACEME` | N/A — same process tracing itself, integrity equal by definition. |
| `PTRACE_ATTACH` / `PTRACE_SEIZE` | At the attach moment. Tracer's integrity must dominate tracee's. |
| Sub-operations on an attached tracee | Inherit attach authority — PIP was checked at attach. |
| `PTRACE_O_TRACECLONE/FORK/VFORK` auto-attach | Child's integrity at fork matches parent's. PIP-compatible inheritance. |
| Tracee exec'ing into a higher-integrity binary | **Trace is dropped.** A trace cannot persist across an integrity bump. |
| `/proc/[pid]/syscall` | Standard /proc access check + PIP. |

This makes ptrace the well-behaved primitive in §13. It fits the access-control model cleanly because it has an explicit attach moment per pair, where dominance is a question with an answer.

## `PTRACE_SECCOMP_GET_FILTER` — additional gate

Reading another process's seccomp filter reveals its defense-in-depth posture — an attacker who can extract a target's filter can find the gaps. Linux requires `CAP_SYS_ADMIN` on top of the ptrace attach for this operation.

On Peios, `PTRACE_SECCOMP_GET_FILTER` requires **`SeDebugPrivilege` regardless of attach status**. Even a same-principal descendant ptrace cannot extract seccomp filters without the privilege.

## /proc/[pid]/syscall

A read-only window into the target's current syscall — shows what syscall the task is currently in, without needing to ptrace-attach. Subject to the standard /proc access check (process SD `PROCESS_QUERY_INFORMATION` right) plus PIP dominance.

Useful for monitoring tools that want to see "what is this process doing right now" without the synchronisation cost of attaching.

## Audit posture

Every successful `PTRACE_ATTACH` / `PTRACE_SEIZE` emits a KMES audit-class event with:

- Tracer principal.
- Tracee process GUID.
- Attach type (`ATTACH` / `SEIZE`).
- Authorization path (`descendant` / `same-principal-and-PtraceScope-0` / `SeDebugPrivilege` / `target-SD-grant`).

`PTRACE_SECCOMP_GET_FILTER` separately emits an audit-class event on each invocation with the requested filter index and the result. This is a high-signal event for forensic reconstruction — extracting seccomp filters is a strong indicator of reconnaissance against a target's hardening.

Sub-operations on an attached tracee (PEEK/POKE/GETREGS/...) are not individually audited — the attach is the gateable moment, and post-attach operations are the natural authority of the tracer-tracee relationship.

## strace, gdb, and the typical paths

Common operational scenarios:

| Scenario | Path | Privilege needed |
|---|---|---|
| `strace mycommand` (run + trace as child) | gdb forks `mycommand`, descendant relationship | None at default `PtraceScope=1`. |
| `strace -p $PID` (attach to running same-principal process) | Cross-process, same-principal | None at `PtraceScope=0`; otherwise `SeDebugPrivilege`. |
| `gdb --pid=$PID` on a daemon running as another principal | Cross-principal | `SeDebugPrivilege` + PIP dominance. |
| `gdb mybinary; r` (run binary under gdb) | Descendant relationship | None. |
| Wine using `PTRACE_SET_SYSCALL_USER_DISPATCH` on its emulated process | Per-tracee, doesn't escalate | None beyond standard ptrace authority. |
| Antivirus extracting seccomp filter from suspected malware | Always | `SeDebugPrivilege`. |

The default `PtraceScope=1` is set so the most common case — debugging your own subprocesses — works without privilege, while the foothold-creation case (one of your processes attacking another) is closed.

## See also

- [`SeDebugPrivilege`](../privileges/debug) — the privilege that overrides `PtraceScope` for cross-process ptrace.
- [PIP](../pip/overview) — Process Integrity Protection, the mandatory dominance check enforced on attach.
- [Instrumentation primitives — uprobes](instrumentation-primitives) — contrasted with ptrace; uprobes have no explicit attach moment and therefore cannot enforce PIP.
- [seccomp](../seccomp/overview-and-design) — the syscall-filtering subsystem whose filter extraction is gated by `SeDebugPrivilege` on top of ptrace.
