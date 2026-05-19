---
title: Process mitigations
type: concept
description: A mitigation is a per-process security hardening flag stored on the PSB. Each flag enables a specific kernel-enforced restriction — what may be made executable, how code is laid out, what control flow is permitted. Mitigations are one-way (they can be tightened but never loosened) and survive exec. This page covers the model and how mitigations differ from access control.
related:
  - peios/process-mitigations/catalog
  - peios/process-mitigations/applying-and-lifecycle
  - peios/process-integrity-protection/overview
  - peios/binary-signing/overview
  - peios/tokens/overview
---

A **mitigation** is a per-process kernel-enforced hardening rule. Where the DACL, PIP, and the access check decide *what objects a process may reach*, mitigations decide *what a process may do with itself* — what regions of its own memory may be made executable, how its address space is laid out, what kinds of indirect control flow are permitted, what it can do with child processes.

Mitigations are stored on the process's PSB (Process Security Block) as a set of boolean flags. The PSB is the same per-process structure that holds the PIP fields and the process SD — covered in [Process integrity protection](~peios/process-integrity-protection/overview). Each mitigation has its own flag; each flag controls one specific kernel-enforced behaviour.

The mitigation model is **one-way**: each flag can be turned on but never turned off. Once a process has enabled WXP (write-XOR-execute), it cannot disable WXP. The flag survives `exec`, so a child binary launched into a process that had enabled the mitigation inherits the constraint.

This page covers the model — what mitigations are, how they fit in alongside the other access-control layers, what the one-way and exec-preservation rules mean, and who sets them.

## What mitigations protect against

Mitigations exist for a different threat model than access control. The DACL protects an object from unauthorised callers; the access check decides whether the caller has the right to act. Mitigations protect a *process* from *its own bugs* and from injected code.

The motivating scenario for most mitigations is the same: a process has a memory-safety bug — a buffer overflow, a use-after-free, an integer overflow — that an attacker exploits to redirect execution. The exploit typically wants to do one of:

- Inject new executable code (shellcode) into the process and jump to it.
- Reuse existing code in unexpected ways (return-oriented programming, jump-oriented programming).
- Hijack indirect branches to land at attacker-chosen targets.
- Modify already-loaded code in place.

Each mitigation closes one or more of these doors. The mechanism is uniform: the kernel refuses the request that would enable the exploit, even though the syscall or memory operation looks legitimate. A process that has enabled WXP cannot mmap a writable-and-executable page; the kernel returns an error. A process with TLP enabled cannot mmap-as-executable a file outside the approved-paths cache; the kernel refuses.

The result is not "the bug is fixed" — the bug is still there, and the exploit may still be able to corrupt memory. What changes is what the exploit can *do* with the corrupted memory. A successful exploit on a process without mitigations gives the attacker arbitrary code execution; the same exploit on a process with mitigations gives the attacker a crashed process (the kernel refused the operation and the process aborts).

## How mitigations differ from access control

The two layers solve different problems:

| | Access control | Mitigations |
|---|---|---|
| **What it gates** | Operations against other objects (files, registry keys, processes) | Operations the process performs on its own memory and address space |
| **Driven by** | Identity and policy (token, SD, privileges) | Hardening posture chosen at process startup |
| **Granularity** | Per-object | Per-process |
| **Adjustability** | Identity can adjust within rules (AdjustPrivileges) | One-way; only ever tightened |
| **Who sets it** | authd (token), object owner / administrator (SD) | The launching process (typically peinit) or the process itself |
| **Threat model** | Untrusted callers reaching trusted objects | Code-execution exploits in the process's own memory |

A process can be subject to both layers simultaneously. A TCB daemon has restrictive access control (only TCB-level callers can interact with it) and a strict set of mitigations (WXP, LSV, TLP, CFI, PIE, SML). The two layers reinforce each other: access control keeps untrusted callers out, mitigations keep the process from being exploited even if untrusted input does reach it.

A process can also be subject to one without the other. An unprotected user-mode binary has no PIP, an open DACL, and no mitigations — it depends on the access control of objects it touches but has no internal hardening. The opposite — strict mitigations with permissive access — is less common in practice but legal.

## The PSB storage and the one-way rule

The mitigations live in a small bitfield on the PSB:

| Flag | Bit value |
|---|---|
| WXP | 0x001 |
| TLP | 0x002 |
| LSV | 0x004 |
| CFI (legacy alias for CFIF + CFIB) | 0x008 |
| UI_ACCESS | 0x010 (reserved) |
| NO_CHILD | 0x020 |
| CFIF | 0x040 |
| CFIB | 0x080 |
| PIE | 0x100 |
| SML | 0x200 |
| ALL | 0x3FF |

Each bit is independent. Setting a bit enables the mitigation; the bit can be set but never cleared. The kernel rejects any operation that would clear a previously-set bit.

The one-way rule is what makes mitigations trustworthy. A process that has WXP enabled cannot be tricked or coerced into disabling it. There is no syscall to clear a mitigation; there is no privilege that bypasses the rule. Once on, on for the lifetime of the process (and beyond — see below).

The same applies to the related flag `no_child_process`, stored alongside on the PSB. Once set, the process can never fork or clone again. There is no way to undo it.

## Exec preservation

When a process execs a new binary, almost everything about the process resets. The address space is wiped, the new binary is mapped, the entry point runs. But the PSB's mitigations **survive exec**. A process that had WXP enabled before exec still has WXP enabled after; the new binary inherits the constraint.

This is the rule that makes the one-way model genuinely one-way. Without exec preservation, an attacker who could control what binary the process execs could trivially "unset" the mitigations by exec'ing a binary in a fresh address space — but the kernel does not give the attacker that escape. The flags travel with the process, not with the binary.

The corollary: a binary that fundamentally cannot operate under a given mitigation (a JIT compiler under WXP, say) cannot be exec'd into a process that has that mitigation set. The exec will succeed (the kernel does not gate exec on mitigations), but the binary's first attempt to do the thing it needs (mmap PROT_EXEC of newly-written code) will fail with the appropriate error. The result is a process that runs the binary's startup code and then crashes when it tries to do its job.

Practical implication: deciding which mitigations to enable is a per-process decision made at startup, based on knowledge of what binary will run there. peinit knows that authd cannot tolerate WXP-incompatible operations because authd was compiled to be WXP-compatible. So peinit sets WXP on the authd process. A process launching arbitrary user binaries cannot make the same assumption; setting WXP on a user shell would break any JIT or self-modifying binary the user happened to run.

## Who sets mitigations

Three patterns for setting mitigations:

- **peinit, before exec.** When peinit launches a service, it forks, sets the desired mitigations on the child's PSB via `kacs_set_psb`, then execs the service binary. The service comes up with the mitigations already in place. This is the standard pattern for system services.
- **The process itself, after startup.** A process can set mitigations on its own PSB. The typical pattern is "after the early-startup work (which may need to relax some constraints), set the mitigations and continue with the constrained code". Self-application of mitigations is a hardening best practice for binaries that have a clear startup-then-steady-state split.
- **A privileged supervisor.** A process with `PROCESS_SET_INFORMATION` on the target and the appropriate PIP dominance can set mitigations on another process. Rare in practice — most mitigation-setting is either at exec time (peinit) or by the process itself.

In all three cases, the call is `kacs_set_psb`. The full mechanics — what fields can be set, what fails, who needs what privilege — are in [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle).

## What the kernel actually does when a mitigation fires

Each mitigation has its own enforcement points. The pattern is the same: a syscall the process is about to make is checked against the relevant mitigation; if the operation would violate the mitigation, the kernel returns an error (typically `-EACCES` or `-EPERM`) rather than performing the operation.

The process can then handle the error. In most cases, encountering a mitigation-blocked operation is unexpected — the process did not anticipate it could happen — and the result is a crash. In some cases, the process handles the error gracefully by falling back to a different code path. The kernel does not decide which; it just refuses the operation.

This is uniform across mitigations:

- WXP refuses `mprotect` calls that would transition pages W→X.
- LSV refuses `mmap(PROT_EXEC)` of unsigned or insufficiently-trusted files.
- TLP refuses `mprotect(PROT_EXEC)` of pages backing files outside approved paths.
- CFIF refuses indirect branches that land outside ENDBR (or equivalent) target instructions.
- PIE refuses exec of non-PIE binaries (this one fires at exec, not at runtime).

Each is enforced by the kernel at the syscall layer. There is no userspace component. The process cannot bypass them by avoiding libc; the syscalls themselves carry the check.

## Where to start

If you want the catalog — what each individual mitigation does, when it fires, what kernel surfaces it covers — read [Catalog](~peios/process-mitigations/catalog).

If you want the operational mechanics — `kacs_set_psb`, the right syscall and privilege requirements, the lifecycle of a mitigation flag from initial set through fork and exec — read [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle).
