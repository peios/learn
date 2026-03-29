---
title: Process Protection
order: 1
---

The AccessCheck section described PIP protecting **objects** — files, registry keys, tokens — from processes that lack sufficient trust. This section describes PIP protecting **processes** — their memory, their execution, their metadata — from other processes.

This is a separate enforcement surface. It does not use AccessCheck, does not read Security Descriptors, and does not involve the DACL pipeline. It is a direct dominance check between two processes' PSBs, enforced at kernel hook sites.

The two surfaces complement each other. Object protection prevents a non-dominant process from opening authd's private key file. Process protection prevents the same process from reading the key directly out of authd's memory via ptrace, or killing authd with a signal.

## The dominance check

Every process isolation check reduces to one question: does the caller's PSB dominate the target's PSB?

```
pip_dominates(caller_psb, target_psb) -> bool:
    return caller_psb.pip_type >= target_psb.pip_type
       AND caller_psb.pip_trust >= target_psb.pip_trust
```

If the target has `pip_type = None`, dominance is trivially true for any caller. The check only restricts access when the target is Protected or Isolated.

Process isolation is binary: dominate or don't. There is no "you can signal this process but not read its memory" granularity. If you dominate, you have full process access. If you don't, you have none.

> [!INFORMATIVE]
> This is deliberately simpler than the object model. Object access has natural categories (read, write, execute). Process access does not — if you can ptrace a process, you can read its memory, inject code, and effectively become it. Partial process access is not a meaningful security boundary.
