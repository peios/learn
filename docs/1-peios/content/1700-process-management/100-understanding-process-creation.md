---
title: Understanding Process Creation
type: concept
description: How Peios creates new processes — the clone primitive, what is inherited, and how identity, integrity, and protection follow a process from fork through exec.
related:
  - peios/identity/how-tokens-work
  - peios/identity/primary-vs-impersonation-tokens
  - peios/process-security/understanding-process-security
  - peios/process-security/process-mitigations
---

Every process on Peios is created by cloning an existing one. There is no separate "spawn a fresh process" primitive — every process descends, ultimately, from PID 1 (peinit), which descends from the kernel's init task. New processes are produced by **fork** (a copy of the calling process) and then transformed by **exec** (a replacement of the program image inside that copy).

This two-step model — clone first, then optionally replace the image — is the foundation of everything from interactive shells to the way peinit launches services.

## The single creation primitive

The kernel exposes one creation primitive: `clone()`. The traditional `fork()` and `vfork()` calls are convenience wrappers around it, and the newer `clone3()` call is the same primitive with an extensible argument struct. Whether a call produces a new **process** or a new **thread** is controlled by a single flag: `CLONE_THREAD`.

| Without `CLONE_THREAD` | With `CLONE_THREAD` |
|---|---|
| Creates a new process | Creates a new thread in the existing process |
| Receives a fresh, independent copy of the parent's primary token | Shares the parent's primary token with sibling threads |
| Receives a new process security descriptor and process GUID | No new process object is created |
| Subject to the parent's `no_child_process` restriction, if set | Not affected by `no_child_process` |
| Impersonation state cleared — the child runs as its primary token | Each thread maintains its own impersonation state |

This branch is the most important fact about process creation on Peios. Almost every property — what is inherited, what is shared, what is reset — depends on which side of it you take.

## What a new process inherits

A process created without `CLONE_THREAD` is a **deep copy** of its parent at the moment of clone. The child receives:

- A copy of the parent's primary token. Subsequent changes to either token are invisible to the other.
- A copy of the parent's address space, file descriptors, signal handlers, and other process state, modulated by the additional `CLONE_*` flags that control sharing.
- The parent's process integrity protection (PIP) settings, including any Protected status. A Protected parent produces a Protected child.
- The parent's process mitigation flags — write-XOR-execute, loader signature verification, and the rest. These persist into the child.
- The parent's `no_child_process` restriction, if set. A process that has been forbidden to create children remains forbidden, regardless of what binary it loads next.

The child does **not** inherit:

- The parent's impersonation token. If the parent thread was running as someone else at the moment of clone, the child still starts as the parent's primary identity. Impersonation is a per-thread concept and never crosses a process boundary.
- The parent's process GUID. Every process is identified by its own kernel-generated UUID — used for audit, supervision, and IPC — and a fresh one is allocated at creation.
- The parent's process security descriptor. A new SD is built for the child from a default template, with the forking thread's primary token's user SID as the owner.

## What exec changes

`exec()` — in any of its forms, `execve`, `execveat`, and the libc-level wrappers — replaces the running program image inside an existing process. It does not create a new process. PID, parent, file descriptors (subject to close-on-exec), and most kernel state survive.

The interesting question is what survives at the *security* level:

- **The primary token survives unchanged.** Identity does not change at exec. A process running as `alice` continues to run as `alice` after exec, regardless of what binary is loaded.
- **Impersonation is dropped.** Any in-progress impersonation is reverted before the new program runs. The new program always starts with the primary token as its effective identity.
- **PIP is recomputed from the new binary.** Process protection follows the binary, not the lineage. A Protected parent that execs an unsigned binary loses protection. A normal parent that execs a signed protected binary gains it.
- **Mitigation flags persist.** Every mitigation set on the parent — including ones added between fork and exec — survives unchanged. There is no way for a binary to opt out of mitigations its caller has already applied.
- **Integrity may be lowered, never raised.** If the token carries the `NEW_PROCESS_MIN` policy and the executable file's integrity label is lower than the token's integrity level, the kernel replaces the token with a fresh copy at the file's integrity level. This is the mechanism behind running medium-integrity browsers from a high-integrity desktop session.

There is no `setuid` bit on Peios. Exec cannot change which user a process is running as. The only paths to a different identity are explicit token assignment by a privileged supervisor (the way peinit assigns service tokens) and explicit impersonation by code that already holds an impersonation token.

## How services receive their identity

Because exec preserves identity, the only way for a service to start under a different token than its parent is for the parent to install one before calling exec. The pattern peinit follows is:

1. **Fork.** The child starts as a copy of peinit, carrying peinit's token (the SYSTEM token, or whatever peinit is running as).
2. **Install the service's token on the child.** peinit calls into the token API to replace the child's primary token with one built specifically for the service — the service's user SID, its group memberships, the privileges and integrity level appropriate to its role.
3. **Exec the service binary.** The kernel notices that no impersonation is active and runs the binary under the new primary token.

This is why "the service's token" is a meaningful concept on Peios. It is not the user token of whoever started peinit, and it is not derived from any UID in the binary's metadata. It is a deliberate, supervisor-assigned identity, decided at service launch and visible in the audit record.

## The first processes

Three processes have special status:

| Process | Role |
|---|---|
| PID 0 (idle) | The per-CPU idle task. One instance per CPU. Runs only when no other task is runnable. Carries the SYSTEM token but never executes user code. |
| Kernel init task | The kernel's bootstrap task. PKM creates the SYSTEM token during kernel initialization and assigns it to this task. |
| PID 1 (peinit) | The first userspace process. Created by exec from the kernel init task and inherits the SYSTEM token. peinit is the ancestor of every other userspace process. |
| Kernel threads (`kthreadd` and children) | Threads created and managed entirely by the kernel. They have no userspace context, never run user code, and operate under the SYSTEM token. |

The SYSTEM token's contents are hardcoded in the kernel (see [How tokens work](../identity/how-tokens-work)). It is not generated from configuration, and no syscall produces it. This is what makes early boot well-defined: PID 1 starts with a known, fixed identity, and every other token in the system is ultimately derived from work peinit (and later authd) does on top of it.

## What can be executed

The kernel directly recognises two classes of executable content:

- **ELF binaries.** The native format. The loader reads the program headers, maps segments, applies mitigations, and transfers control to the entry point.
- **Script interpreters (`#!`).** A file beginning with `#!/path/to/interpreter` causes the kernel to exec the interpreter with the script as its first argument. The interpreter is what actually runs; the script's identity comes from the exec call, not from the interpreter.

A third class — **registered handlers** that match arbitrary files by magic number or extension and route them to a specified interpreter — is covered on its own page once the design is settled.

## Restrictions on creation

Process creation is not unconditional. Three mechanisms can block it:

- **`no_child_process`.** A flag in the process security block that, once set, forbids the process from ever creating a new process. Threads are still allowed. The flag persists across exec, so a confined service cannot escape it by reloading.
- **AccessCheck on the parent.** Operations against a running process — sending signals, reading memory, attaching a debugger — go through the parent's access control on every call. A process cannot meaningfully create a child it would not otherwise be allowed to interact with.
- **Mitigations enforced at load.** When exec runs, the binary's mitigation requirements are evaluated. A binary that requires mitigations the runtime environment cannot satisfy will fail to load.

Together, these mechanisms make process creation a discretely auditable event with predictable security properties: a known parent, a known token, a known SD, and a known set of restrictions, all decided before the new program runs its first instruction.
