---
title: Process Security Descriptors
order: 3
---

Every process carries a security descriptor that controls who can perform operations on it. This replaces Linux's UID-based process access control (which is a patchwork of UID comparisons and capabilities) with unified SD evaluation.

## Process access rights

| Right | Value | Meaning |
|---|---|---|
| PROCESS_TERMINATE | 0x0001 | Send lethal signals (SIGKILL, SIGTERM, SIGABRT, SIGQUIT). |
| PROCESS_SIGNAL | 0x0002 | Send non-lethal signals (SIGHUP, SIGUSR1, SIGCONT, etc.). |
| PROCESS_VM_READ | 0x0010 | Read process memory (ptrace peek, `/proc/<pid>/mem`, `process_vm_readv`). |
| PROCESS_VM_WRITE | 0x0020 | Write process memory (ptrace poke, `/proc/<pid>/mem`, `process_vm_writev`). Includes debugger attach. |
| PROCESS_DUP_HANDLE | 0x0040 | Extract file descriptors from the process (`pidfd_getfd`). |
| PROCESS_QUERY_INFORMATION | 0x0400 | Inspect the process's token, read detailed `/proc/<pid>/*` files (maps, status, fd, environ). |
| PROCESS_QUERY_LIMITED | 0x1000 | Read basic process information: PID, image name, state, CPU/memory usage. This is the level visible in `ps` and `top`. |
| PROCESS_SET_INFORMATION | 0x0200 | Change process priority, CPU affinity, I/O priority, resource limits. |
| READ_CONTROL | 0x20000 | Read the process's own SD. |
| WRITE_DAC | 0x40000 | Modify the process's DACL. |
| WRITE_OWNER | 0x80000 | Change the process's SD owner. |

## Generic mapping

| Generic right | Maps to |
|---|---|
| GENERIC_READ | PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ \| READ_CONTROL |
| GENERIC_WRITE | PROCESS_SET_INFORMATION \| PROCESS_VM_WRITE \| WRITE_DAC |
| GENERIC_EXECUTE | PROCESS_TERMINATE \| PROCESS_QUERY_LIMITED |
| GENERIC_ALL | All process rights |

## Default process SD

Processes MUST receive a default SD at creation time:

```
Owner: <creator's user SID>
Group: <creator's primary group SID>
DACL:
  ALLOW  <process's own user SID>        GENERIC_ALL
  ALLOW  BUILTIN\Administrators           GENERIC_ALL
  ALLOW  SYSTEM                            GENERIC_ALL
  ALLOW  Everyone                          PROCESS_QUERY_LIMITED
```

This means:

- The process can do anything to itself.
- Administrators and SYSTEM have full control over all processes.
- Everyone can see basic process info (PID, name, status) -- this is what makes `ps` and `top` work for all users.
- Detailed inspection (token, memory, environment) is restricted to self, administrators, and SYSTEM.

Services MAY request a custom SD at launch (via the service definition), or modify their own SD at runtime (via `kacs_set_sd` on their own process, which requires WRITE_DAC -- granted by the default SD to the process itself).

## PIP interaction

PIP and the process SD are complementary. The process SD controls *who* can perform operations on the process. PIP controls *which trust level is required* for invasive access to protected processes. Both checks MUST pass:

1. AccessCheck evaluates the caller's token against the target process's SD for the requested right.
2. PIP evaluates the caller's trust level against the target's `pip_type` and `pip_trust` (for operations that cross the process boundary).

A process MAY have a permissive SD (Administrators: GENERIC_ALL) but be PIP-protected -- administrators pass the SD check, but only if their PIP trust level is sufficient. Conversely, a non-PIP process MAY have a restrictive SD that denies even administrators specific operations.
