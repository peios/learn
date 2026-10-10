---
title: Process mitigations
type: concept
description: A mitigation is a one-way, kernel-enforced hardening flag on the PSB — restricting what a process may do with its own memory, control flow, and children.
related:
  - peios/process-mitigations/catalog
  - peios/process-mitigations/applying-and-lifecycle
  - peios/process-integrity-protection/overview
  - peios/binary-signing/overview
  - peios/tokens/overview
---

A **mitigation** is a per-process kernel-enforced hardening rule. Where the DACL, PIP, and the access check decide *what objects a process may reach*, mitigations decide *what a process may do with itself* — what regions of its own memory may be made executable, how its address space is laid out, what kinds of indirect control flow are permitted, what it can do with child processes.

Mitigations are stored on the process's PSB (Process Security Block) as a set of boolean flags. The PSB is the same per-process structure that holds the PIP fields and the process SD — covered in [Process integrity protection](~peios/process-integrity-protection/overview). Each mitigation has its own flag; each flag controls one specific kernel-enforced behaviour.

The mitigation model is **one-way**: each flag can be turned on but never turned off. Once a process has enabled WXP (write-XOR-execute), it cannot disable WXP. The flag survives `exec`, so a replacement binary runs under the process's existing constraints. Children inherit committed flags at fork.

This page covers the model: what mitigations are, how they fit alongside access control, and why lifecycle boundaries matter. For an operational check, start with [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle): inspect the running process, compare its committed flags with the required policy, and keep a failed request separate from verified protection.

A flag in a catalog or launch configuration is not proof it is active. The [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#process-mitigations-one-way) describes activation-backed, all-or-nothing application and current implementation limits. In particular, it documents CFIF as unavailable and CFIB activation as self-only. Check those limits before interpreting a requested hardening set.

## What mitigations protect against

Mitigations exist for a different threat model than access control. The DACL protects an object from unauthorised callers; the access check decides whether the caller has the right to act. Mitigations protect a *process* from *its own bugs* and from injected code.

The motivating scenario for most mitigations is the same: a process has a memory-safety bug — a buffer overflow, a use-after-free, an integer overflow — that an attacker exploits to redirect execution. The exploit typically wants to do one of:

- Inject new executable code (shellcode) into the process and jump to it.
- Reuse existing code in unexpected ways (return-oriented programming, jump-oriented programming).
- Hijack indirect branches to land at attacker-chosen targets.
- Modify already-loaded code in place.

Each mitigation closes one or more of these doors. The mechanism is uniform: the kernel refuses the request that would enable the exploit, even though the syscall or memory operation looks legitimate. A process that has enabled WXP cannot mmap a writable-and-executable page; the kernel returns an error. A process with TLP enabled cannot mmap-as-executable a file outside the approved-paths cache; the kernel refuses.

The result is not "the bug is fixed" — the bug is still there, and the exploit may still be able to corrupt memory. What changes is what the exploit can *do* with the corrupted memory. An exploit may be stopped at a refused operation or cause a process fault instead of achieving code execution. That is a defence against particular exploitation paths, not a guarantee that every exploit is stopped or that every refusal crashes the process.

## How mitigations differ from access control

The two layers solve different problems:

| | Access control | Mitigations |
|---|---|---|
| **What it gates** | Operations against other objects (files, registry keys, processes) | Operations the process performs on its own memory and address space |
| **Driven by** | Identity and policy (token, SD, privileges) | Hardening posture chosen at process startup |
| **Granularity** | Per-object | Per-process |
| **Adjustability** | Identity can adjust within rules (AdjustPrivileges) | One-way; only ever tightened |
| **Who sets it** | authd (token), object owner / administrator (SD) | The launching process or the process itself |
| **Threat model** | Untrusted callers reaching trusted objects | Code-execution exploits in the process's own memory |

A process can be subject to both layers simultaneously. A TCB daemon can have restrictive access control and a required hardening policy covering memory, libraries, control flow, address layout and speculation. Its actual mitigation set still depends on successful activation; neither its signing level nor the desired policy proves those flags are on. The two layers reinforce each other: access control keeps untrusted callers out, mitigations keep the process from being exploited even if untrusted input does reach it.

PIP, the process descriptor and mitigations are independent dimensions. A process without PIP can still have a restrictive descriptor and committed mitigations. For example, exec of an unsigned binary can remove PIP while preserving the process descriptor and mitigation flags. Inspect each relevant surface rather than inferring an open DACL or absent hardening from the lack of PIP.

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

The table identifies the request bits, not a set that every platform can enable. CFI expands to CFIF and CFIB and is not stored as a separate active flag; UI_ACCESS is reserved; ALL is the accepted-request mask. The [ABI catalog](~peios/advanced-peios/peios-kernel/kacs/kacs-abi#process-mitigation-bits) is the numeric reference.

Before committing a new mitigation, the kernel must activate or verify its protection. If any requested protection fails, the request changes no bits. Previously committed flags cannot be cleared or weakened; requesting only a subset does not remove the rest.

The one-way rule is what makes mitigations trustworthy. A process that has WXP enabled cannot be tricked or coerced into disabling it. There is no syscall to clear a mitigation; there is no privilege that bypasses the rule. Once on, on for the lifetime of the process (and beyond — see below).

The same applies to `NO_CHILD` — bit `0x020` in the same bitfield. Once set, the process cannot fork or clone a new process. Creating threads with `CLONE_THREAD` remains possible. There is no way to clear the restriction.

## Exec preservation

When a process execs a new binary, almost everything about the process resets. The address space is wiped, the new binary is mapped, the entry point runs. But the PSB's mitigations **survive exec**. A process that had WXP enabled before exec still has WXP enabled after; the new binary inherits the constraint.

This is the rule that makes the one-way model genuinely one-way. Without exec preservation, an attacker who could control what binary the process execs could trivially "unset" the mitigations by exec'ing a binary in a fresh address space — but the kernel does not give the attacker that escape. The flags travel with the process, not with the binary.

Preservation is not a promise that the new binary will work. PIE explicitly rejects a non-PIE binary at exec. Other constraints may reject operations the new program needs, such as a JIT attempting to make writable code executable under WXP, or a library load failing LSV or TLP. Check the actual failing operation rather than assuming exec always succeeds and only later operations can fail.

Practical implication: choose the policy with knowledge of the program and its launch path. A service launcher can request the protections its service requires and check the result. A launcher of arbitrary user binaries cannot assume every program is compatible: applying WXP to a shell's process lineage can prevent JIT or self-modifying programs from working.

## Who sets mitigations

Three patterns for setting mitigations:

- **The launcher, before exec.** The launcher's code running in the newly forked child can request compatible mitigations before exec and check the result. This is the between-fork-and-exec pattern described by the Kernel TRM. It is self-application in the child, distinct from the parent modifying another task.
- **The process itself, during startup.** A program can request protections for its own PSB, preferably before untrusted input. Late application must validate existing state; it cannot exempt incompatible startup mappings simply because they were created before the request.
- **An authorised supervisor.** A caller with `PROCESS_SET_INFORMATION` and PIP dominance can request changes to another process. Authority does not bypass activation limits: the Kernel TRM documents CFIB as self-only and CFIF as unavailable.

These are application patterns, not evidence of the service launcher's behavior. The [source-checked peinit 0.0.12 launch path](~peios/boot-and-trust-establishment/peinit-pid-1#service-mitigation-limits) does not apply an additional per-service mitigation mask. Inherited or self-applied flags may still be present; inspect the running process rather than inferring protection from its launcher's identity.

In each case, success must be checked and committed state verified. [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle) explains that evidence; the existing [SDK reference](~peios/sdk-processes/process-h#setting-mitigations) holds the programming interface.

## What the kernel actually does when a mitigation fires

Each mitigation has its own enforcement points. Memory and process-operation checks can refuse a syscall with an error such as `EACCES` or `EPERM`. Architecture-backed protections operate through hardware and kernel support; a control-flow violation can fault rather than return a syscall error.

The process can then handle the error. In most cases, encountering a mitigation-blocked operation is unexpected — the process did not anticipate it could happen — and the result is a crash. In some cases, the process handles the error gracefully by falling back to a different code path. The kernel does not decide which; it just refuses the operation.

The protections address different operations:

- WXP refuses `mprotect` calls that would transition pages W→X.
- LSV refuses `mmap(PROT_EXEC)` of unsigned or insufficiently-trusted files.
- TLP refuses `mprotect(PROT_EXEC)` of pages backing files outside approved paths.
- Forward CFI is intended to reject indirect branches outside designated targets such as ENDBR instructions. The Kernel TRM currently documents CFIF activation as unavailable; do not count it as active merely because it was requested.
- PIE refuses exec of non-PIE binaries (this one fires at exec, not at runtime).

These protections depend on kernel enforcement and, where applicable, architecture support rather than cooperation from libc. Avoiding libc does not bypass kernel checks. A named protection still has to be supported and successfully committed before it can be relied on.

## Where to start

If you want the catalog — what each individual mitigation does, when it fires, what kernel surfaces it covers — read [Catalog](~peios/process-mitigations/catalog).

To inspect actual hardening, understand a refused request, or check what survives fork and exec, read [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle). Use its links to the command, SDK and Kernel TRM references for the corresponding interfaces.
