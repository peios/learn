---
title: Understanding Process Security
type: concept
order: 10
description: How every process carries a security descriptor that governs signals, memory access, debugging, and token inspection.
---

Every process on Peios carries a **security descriptor** that controls who can interact with it. Sending signals, reading memory, attaching a debugger, inspecting tokens — all of these operations are governed by the process's SD, evaluated by the same AccessCheck used for files and every other object type.

## Process access rights

Processes define their own set of specific access rights:

| Right | Meaning |
|---|---|
| `PROCESS_TERMINATE` | Send lethal signals (SIGKILL, SIGTERM, etc.) |
| `PROCESS_SIGNAL` | Send non-lethal signals (SIGHUP, SIGUSR1, SIGCONT, etc.) |
| `PROCESS_VM_READ` | Read process memory |
| `PROCESS_VM_WRITE` | Write process memory (includes debugger attach) |
| `PROCESS_DUP_HANDLE` | Extract file descriptors from the process |
| `PROCESS_QUERY_INFORMATION` | Inspect the process's token, read detailed `/proc` files |
| `PROCESS_QUERY_LIMITED` | Read basic process information (PID, name, state, resource usage) |
| `PROCESS_SET_INFORMATION` | Change process priority, CPU affinity, resource limits |

Standard rights (DELETE, READ_CONTROL, WRITE_DAC, WRITE_OWNER) apply to process SDs just as they do to files.

## The default process SD

Most processes receive a default SD at creation time:

```
Owner: <creator's user SID>
DACL:
  Allow  <process's own user SID>   PROCESS_ALL_ACCESS
  Allow  Administrators              PROCESS_ALL_ACCESS
  Allow  SYSTEM                      PROCESS_ALL_ACCESS
```

This means the process owner, Administrators, and SYSTEM can fully interact with the process. Other principals have no access unless the DACL is modified.

## Process SDs and PIP

The process SD and PIP protection are **separate layers**. The SD controls who has access through the DACL. PIP adds an additional dominance check that cannot be bypassed by privileges.

A non-PIP-protected process is governed entirely by its SD. A PIP-protected process is governed by both — the caller must satisfy the DACL **and** dominate the process's PIP level. Having `PROCESS_VM_READ` granted by the DACL is not enough if the caller fails the PIP dominance check.

## Tightening a process SD

Services can tighten their own SD after initialization. A service that has finished setting up and no longer needs to be managed by Administrators can remove that ACE from its process SD:

```
Owner: S-1-5-80-2739571183 (DNS Service)
DACL:
  Allow  S-1-5-80-2739571183 (DNS Service)  PROCESS_ALL_ACCESS
  Allow  S-1-5-18 (SYSTEM)                   PROCESS_ALL_ACCESS
```

Now only the service itself and SYSTEM can interact with the process. Even Administrators cannot send signals or read memory — they would need to take ownership first (using `SeTakeOwnershipPrivilege`) and then modify the DACL.

This is a defense-in-depth measure. A service that handles sensitive data can reduce its process SD to the minimum needed for ongoing operation.
