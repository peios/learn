---
title: Applying and lifecycle
type: concept
description: Mitigations are set via kacs_set_psb. The call can target the calling process (free, anyone can do it) or another process (requires PROCESS_SET_INFORMATION plus PIP dominance). Once set, a mitigation persists through fork and exec and cannot be cleared. This page covers the syscall, the privileges, and the full lifecycle.
related:
  - peios/process-mitigations/overview
  - peios/process-mitigations/catalog
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-two-check-rule
  - peios/tokens/overview
---

Setting mitigations is a small kernel operation — call a syscall, pass a bitmask, the kernel sets the bits on the PSB. The complications are not in the call itself; they are in who can make the call, when in a process's life it can be made, and how the resulting state propagates through fork and exec.

This page covers the operational mechanics: the `kacs_set_psb` syscall, the privilege rules for setting mitigations on another process, and the lifecycle of a mitigation flag from initial set through process exit.

## kacs_set_psb

The kernel exposes one syscall for setting mitigations:

```
kacs_set_psb(target_pidfd, flags)
```

`target_pidfd` is a pidfd for the process whose PSB is to be modified. The caller's own process is acceptable; another process is also acceptable (subject to privilege rules below).

`flags` is a bitmask combining the values from the catalogue:

| Flag | Bit |
|---|---|
| WXP | 0x001 |
| TLP | 0x002 |
| LSV | 0x004 |
| CFI (legacy alias) | 0x008 |
| UI_ACCESS | 0x010 |
| NO_CHILD | 0x020 |
| CFIF | 0x040 |
| CFIB | 0x080 |
| PIE | 0x100 |
| SML | 0x200 |
| ALL | 0x3FF |

The kernel ORs the flags into the target's existing mitigation bitfield. There is no "clear" — bits cannot be removed. Calling `kacs_set_psb` with a subset of currently-set bits leaves the previously-set bits intact; you can never use this call to disable a mitigation.

The kernel rejects:

- A pidfd pointing at a process the caller does not have authority to modify (see below).
- Unknown flag bits (anything outside the defined set is `-EINVAL`).

The kernel does **not** reject:

- A call setting bits that are already set. The OR is idempotent.
- A call setting `UI_ACCESS` (which is reserved). It sets the bit; the bit has no effect.
- A call setting flags incompatible with the current binary's capabilities. Setting WXP on a process running a JIT is allowed; the JIT will fail the next time it tries to flip a page, but the `kacs_set_psb` call itself succeeds.

## Self versus another process

The privilege required depends on whose PSB is being modified:

**Setting mitigations on your own process** requires no privilege. Any process can call `kacs_set_psb` with its own pidfd (or, more commonly, with no pidfd to mean "self"). The call always succeeds for self-targeted invocations, regardless of identity, integrity, or anything else.

The reasoning: a process can only ever *tighten* its own constraints. There is no risk in letting a process restrict itself further. The model assumes that any code running in the process is, by definition, code the process has chosen to run; that code wanting to add a mitigation is fine.

**Setting mitigations on another process** requires:

- `PROCESS_SET_INFORMATION` on the target process — granted by the target's process SD.
- PIP dominance over the target (per the [two-check rule](~peios/process-integrity-protection/the-two-check-rule)).

This is the standard cross-process operation pattern. The caller's PSB must dominate the target's, and the target's SD must grant the appropriate right to the caller. Both must be satisfied.

In practice this means the only common caller for cross-process `kacs_set_psb` is **peinit** (when launching a service that needs mitigations applied at exec). peinit has TCB-level PIP and is granted `PROCESS_SET_INFORMATION` on the services it launches; it sets the desired mitigations on the child's PSB after fork and before exec.

A self-applied mitigation does not require the caller to be the process itself in the strict sense — it just requires the pidfd to point at the caller's own process. A thread within a process can set mitigations on the process's PSB regardless of which thread does the call.

## Where in the process lifecycle

A mitigation can be set at any moment during a process's life. The kernel does not require it to happen at startup, before exec, or before any specific event. Practical patterns:

- **At process creation, before exec.** peinit forks, calls `kacs_set_psb` on the child's pidfd, then execs the service binary. The mitigations are in place when the binary starts running. This is the standard.
- **At the entry point of the binary.** The binary itself, immediately on startup, sets its desired mitigations on its own PSB. Suitable for binaries that are self-aware about their hardening posture.
- **After early-stage initialisation.** A process that has work to do during early startup that needs to relax some constraints (loading executable libraries from non-approved paths, for example) waits until after that work is done, then sets the mitigation.

A mitigation set late in a process's life closes off only future operations. Operations that have already happened — pages already mapped, libraries already loaded — are not retroactively checked. WXP set after the process has already mmap'd a writable-executable region does not unmap that region; it only refuses *future* such operations.

This is sometimes a useful pattern: a process needs WXP-incompatible behaviour during startup (say, runtime code generation for initialisation) and then transitions to a steady state where WXP is appropriate. The pattern is "do the WXP-incompatible work first, then `kacs_set_psb(self, WXP)`". From that point forward, WXP is enforced.

## Fork: inheritance

When a process forks, the child inherits the parent's mitigation flags exactly. Every bit set on the parent is set on the child. The child cannot un-set them at fork time; the one-way rule applies.

This is the natural extension of one-way: a process that has chosen to lock down its execution cannot give its children more authority than it has itself. If WXP is set, every child also has WXP. If `NO_CHILD` is set... well, the parent cannot fork in the first place, so the question does not arise.

Threads (CLONE_THREAD-style clones) share the parent's PSB rather than copying it. A new thread in the same process is bound by the same mitigations; setting a mitigation in one thread is visible to all threads immediately.

## Exec: preservation, with one wrinkle

When a process execs, all of:

- The process identity (token) — preserved.
- The PIP fields — re-computed from the new binary's signature.
- The process SD — typically preserved, may be re-defaulted if the user identity changed.
- The mitigation flags — **preserved**.

The new binary runs with whatever mitigations were on the PSB before exec. There is no way for exec to relax mitigations.

The one wrinkle: PIE.

PIE is the mitigation that fires *at* exec, not at runtime. With PIE set, the kernel checks the new binary's ELF flags during exec; if the binary is not PIE-built, the exec fails with `-EACCES`. The process attempting the exec sees its `execve` return with an error and continues running its current binary.

For other mitigations, the exec succeeds and the new binary inherits the mitigation. PIE is the one that can cause exec itself to fail.

This means setting PIE before launching a service is a way of saying "this service binary must be PIE, or it cannot run". If the operator updates the service to a binary that is not PIE, the next exec attempt will fail and the service will not start. This is sometimes desired (a hard constraint that the binary be PIE); sometimes inconvenient (an emergency rebuild that lost the PIE flag).

## NO_CHILD and the lifecycle interaction

`NO_CHILD` (bit 0x020) is also stored on the PSB and follows the same one-way rules as the other mitigations. Once set, the process cannot fork or clone-with-new-process.

The lifecycle interaction worth knowing: a process that wants to set up children and then lock itself down should do the forks *first*, then call `kacs_set_psb(self, NO_CHILD)`. After that call, the process cannot create more processes.

If a process needs to be able to fork on demand (a server that handles each connection in a new process), `NO_CHILD` is not appropriate. The fork capability and `NO_CHILD` are mutually exclusive in steady state.

A process with `NO_CHILD` set can still call `exec` (replacing itself with a new binary in the same process) and create threads via `CLONE_THREAD`. The mitigation specifically blocks the spawning of *new* processes.

## Querying mitigations

A process can read its own mitigation flags via the PSB query. The interface — typically through `kacs_open_self_token` and a query on the PSB — returns the current flag bitfield.

For reading another process's flags, the same `PROCESS_QUERY_INFORMATION` + PIP dominance rules apply as for setting them. Typically only peinit or a debug tool would read another process's mitigation flags.

Note that the flags are independent of the PSB's other fields. Querying the mitigation flags does not reveal anything about the process's PIP level, its SD, or its `no_child_process` state — those are separate queries. The mitigation bitfield is its own thing.

## What happens at process exit

A process's PSB is destroyed when the process exits. The mitigation flags vanish with it. There is no persistence; the next time the same binary is exec'd in a fresh process, the mitigations have to be re-applied.

This is why launchers (peinit) apply mitigations on every launch. There is no cached "this binary always gets these mitigations" — every fresh process starts from the inherited PSB, which is whatever the launcher's PSB had plus whatever the launcher chose to add.

The corollary: a process whose launcher does not apply mitigations runs without them, regardless of the binary's intent. A binary that wants to be hardened should also call `kacs_set_psb` at its own entry point so the mitigations are guaranteed regardless of who launched it. Defence in depth: both the launcher and the binary should set the mitigations they need.

## Errors

`kacs_set_psb` can fail with:

| Error | Cause |
|---|---|
| `-EBADF` | Invalid pidfd. |
| `-ESRCH` | The target process has exited. |
| `-EACCES` | The caller does not have `PROCESS_SET_INFORMATION` on the target. |
| `-EPERM` | The caller does not PIP-dominate the target (when modifying another process). |
| `-EINVAL` | Unknown flag bits in `flags`. |

In normal operation, the call succeeds. Failures are typically programming errors (wrong pidfd) or insufficient authority (a low-trust caller trying to modify a high-trust target).
