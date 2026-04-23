---
title: Process Protection
---

The AccessCheck section described PIP protecting **objects** — files, registry keys, tokens — from processes that lack sufficient trust. This section describes PIP protecting **processes** — their memory, their execution, their metadata — from other processes.

Process-to-process operations are gated by **two independent checks**, both of which MUST pass:

1. **Process SD check** — an AccessCheck evaluation of the caller's token against the target process's Security Descriptor (see the Process Security Descriptors section). This determines *who* can perform operations on the process.
2. **PIP dominance check** — a direct comparison of the caller's and target's PSB pip_type/pip_trust fields. This determines *which trust level is required*. PIP does not use AccessCheck, does not read Security Descriptors, and does not involve the DACL pipeline — it is a standalone binary dominance test.

SeDebugPrivilege bypasses only check 1 (the process SD). It MUST NOT bypass check 2 (PIP dominance). See the Enforcement Points section for details.

The two checks complement each other. The process SD controls *who* can access the process (identity-based). PIP controls *which trust level is required* (signing-based). Object PIP protection (via trust label ACEs in SACLs) prevents a non-dominant process from opening authd's private key file. Process PIP protection prevents the same process from reading the key directly out of authd's memory via ptrace, or killing authd with a signal.

## The dominance check

Every process isolation check reduces to one question: does the caller's PSB dominate the target's PSB?

```
pip_dominates(caller_psb, target_psb) -> bool:
    if target_psb.pip_type == None:
        return true  // Unprotected target — any caller dominates.
    return caller_psb.pip_type >= target_psb.pip_type
       AND caller_psb.pip_trust >= target_psb.pip_trust
```

PIP types form a total order by their numeric values: None (0) < Protected (512) < Isolated (1024). PIP trust levels are numeric and compared directly (higher = more trusted). The early return for `pip_type = None` ensures that unprotected processes are always accessible regardless of trust values. The two-dimension check only applies when the target is Protected or Isolated.

PIP dominance is binary: dominate or don't. If you don't dominate, you have no process access via PIP — the operation is denied regardless of which specific operation was attempted. The process SD provides per-operation granularity (different access rights for signals vs memory vs metadata); PIP is the all-or-nothing gate on top of the SD check. Both MUST pass.

> [!INFORMATIVE]
> This is deliberately simpler than the object model. Object access has natural categories (read, write, execute). Process access does not — if you can ptrace a process, you can read its memory, inject code, and effectively become it. Partial process access is not a meaningful security boundary.
