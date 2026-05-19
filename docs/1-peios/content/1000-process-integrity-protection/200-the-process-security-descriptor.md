---
title: The process security descriptor
type: concept
description: Every running process has its own security descriptor — separate from the security descriptors of its files, its registry keys, or its tokens. The process SD lives on the PSB and gates operations that act on the process itself. This page covers what the process SD contains, the access rights it uses, how it interacts with PIP, and how it is set and modified.
related:
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-two-check-rule
  - peios/security-descriptors/overview
  - peios/tokens/overview
---

A process is an object the kernel protects, like any other. It carries a security descriptor — the **process SD** — that defines who can do what *to* this process. Where the token's SD controls who can do what to the token (read, duplicate, impersonate), the process SD controls who can act on the running process itself: signal it, debug it, inspect its memory, change its priority, open its tokens.

The process SD sits on the PSB, not the token. The token's SD is a separate field, governing token operations. The two are distinct objects with distinct policies. A change to one does not affect the other.

This page covers what the process SD contains, the access rights it uses, how it is created, and how it is modified. The dominance pairing — how the process SD plus PIP forms the two-check rule — is in [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).

## What the process SD contains

The process SD has the same shape as any other SD — owner, primary group, DACL, optional SACL. The fields mean the same things they mean elsewhere (see [Security descriptors](~peios/security-descriptors/overview)). What differs is the **access rights** the DACL grants.

The DACL on a process SD uses the **process access rights** — a set of 16-bit object-specific rights tailored to what one might do to a process. The full list:

| Right | Value | What it gates |
|---|---|---|
| `PROCESS_TERMINATE` | 0x0001 | Send terminating signals (SIGKILL, SIGTERM, SIGABRT, etc.). |
| `PROCESS_SIGNAL` | 0x0002 | Send non-terminating informational signals (SIGCHLD, SIGURG, SIGWINCH, etc.). |
| `PROCESS_VM_READ` | 0x0010 | Read the process's memory. Required by `ptrace(PTRACE_PEEK*)`, `process_vm_readv`, `/proc/<pid>/mem` reads. |
| `PROCESS_VM_WRITE` | 0x0020 | Write the process's memory. Required by `ptrace(PTRACE_POKE*, PTRACE_ATTACH)`, `process_vm_writev`, `/proc/<pid>/mem` writes. |
| `PROCESS_DUP_HANDLE` | 0x0040 | Duplicate file descriptors out of the process via `pidfd_getfd`. |
| `PROCESS_SET_INFORMATION` | 0x0200 | Change process attributes — scheduling priority, CPU affinity, rlimits, certain `/proc/<pid>/*` writes. |
| `PROCESS_QUERY_INFORMATION` | 0x0400 | Read detailed process information — token, full `/proc/<pid>/*` reads (cmdline, status, io, limits, sched, mounts). |
| `PROCESS_SUSPEND_RESUME` | 0x0800 | Send stop/continue signals (SIGSTOP, SIGCONT). |
| `PROCESS_QUERY_LIMITED` | 0x1000 | Read limited process information (PID, image name, basic state). Required by `pidfd_open`. |

Plus the standard rights — `DELETE`, `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER`, `SYNCHRONIZE` — and the special rights `ACCESS_SYSTEM_SECURITY` and `MAXIMUM_ALLOWED`. These mean the same things on a process as on any other object.

`PROCESS_TERMINATE` and `PROCESS_SIGNAL` are split because terminating signals are operationally different from informational ones. A monitoring tool might be allowed to send SIGCHLD-style signals without being allowed to kill the process. This is the kind of decomposition the process rights catalogue makes possible.

## Generic mapping

The standard generic rights (`GENERIC_READ`, `GENERIC_WRITE`, `GENERIC_EXECUTE`, `GENERIC_ALL`) map to combinations of process-specific rights:

| Generic right | Process-specific equivalent |
|---|---|
| `GENERIC_READ` | `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | READ_CONTROL` |
| `GENERIC_WRITE` | `PROCESS_SET_INFORMATION | PROCESS_VM_WRITE | WRITE_DAC` |
| `GENERIC_EXECUTE` | `PROCESS_TERMINATE | PROCESS_SUSPEND_RESUME | PROCESS_QUERY_LIMITED` |
| `GENERIC_ALL` | All process-specific rights plus all standard rights. |

A DACL ACE that grants `GENERIC_READ` to some principal effectively grants them the right to read the process's memory, query its detailed information, and read the SD itself. A DACL granting `GENERIC_EXECUTE` lets them terminate or suspend the process. These are the abstractions tools use when they say "grant read access to this process" without enumerating every specific right.

## How the process SD is created

A new process's SD is set up at process creation. The path:

1. **At fork**, the child inherits a copy of the parent's process SD. The child's process is a different object from the parent's, but the SD is structurally the same.
2. **At exec**, if the new binary's signing changes the PIP fields significantly (in particular, if the new PIP type is non-zero where the old was zero, or if a `KACS_IOC_INSTALL` of a different user-identity token happens between fork and exec), the kernel may regenerate the process SD from a default template based on the new token's identity. The intent is that a process running a TCB binary should have a TCB-flavoured process SD, not whatever its parent had.
3. **The default template**, when used, grants the process's user identity `PROCESS_QUERY_LIMITED` and `PROCESS_QUERY_INFORMATION`, grants `BUILTIN\Administrators` and `SYSTEM` the right to inspect and signal, and denies everything else to ordinary callers.

For typical user processes, the SD that ends up on the PSB is the inherited copy of the parent's. For TCB processes — the daemons signed at TCB trust level — the SD is regenerated to reflect the role of the process.

## How the process SD is modified

The process SD on a running process can be updated via `kacs_set_sd` on the PSB, just like setting an SD on a file. The caller needs `WRITE_DAC` on the target process (for the DACL) and the appropriate rights for owner, group, and SACL changes. The standard SD modification rules from [Security descriptors](~peios/security-descriptors/overview) apply.

A common use case: a service whose SD needs to be tightened after startup. The service launches with a default SD that lets the supervisor inspect and signal it; once the service is in steady state, it tightens its own SD to remove some of those rights, restricting which external callers can affect it.

Another use case: a process voluntarily allowing another to debug it. Adding an ACE granting `PROCESS_VM_READ | PROCESS_VM_WRITE` to a specific helper SID lets that helper attach a debugger without administrator intervention.

The process SD does **not** affect PIP. Changing the SD does not change the PIP fields. The two are independent — the SD-on-PSB gates "who is allowed" while PIP gates "what trust level is allowed". A debugger added to the SD still needs to PIP-dominate the target to actually debug it.

## What the process SD does *not* do

A few clarifications:

- **The process SD does not gate the process's own access to objects.** It controls operations *targeting* the process. What the process itself can do is governed by its token, not by its own SD. A process can be `PROCESS_TERMINATE`-denyed by its own SD (other processes can't kill it) while still being free to do whatever its token allows.
- **The process SD does not replace PIP.** A non-PIP-protected process can have a restrictive SD; an inspector granted `PROCESS_VM_READ` by the SD can still read its memory if PIP permits. A PIP-protected process needs both the SD grant AND PIP dominance — see [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).
- **The process SD does not control file access.** Each open file has its own SD; the process's SD is unrelated to what files the process can open.
- **The process SD does not control token operations.** The token has its own SD; opening or duplicating tokens goes through that, not the process SD (although the token operations also check process-level rights as a wrapper — `kacs_open_process_token` requires `PROCESS_QUERY_INFORMATION` on the process AND the appropriate right on the token).

The cleanest mental model: the process SD answers "may I (the caller) signal, debug, or inspect that process?". Everything else about the process's behaviour, identity, and authority lives in other SDs or in the token.
