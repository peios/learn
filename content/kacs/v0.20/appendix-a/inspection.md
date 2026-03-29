---
title: Inspection Interfaces
order: 4
---

## procfs

**`/proc/<pid>/token`** — displays the primary token of process `<pid>`. Gated by PROCESS_QUERY_INFORMATION on the target process's SD, plus PIP trust level comparison for protected processes. Reading `/proc/self/token` is always allowed.

**`/proc/<pid>/task/<tid>/token`** — displays the effective token of thread `<tid>`. Shows the impersonated token if the thread is impersonating.

## securityfs

**`/sys/kernel/security/kacs/self`** — the calling thread's effective token. Always readable.

**`/sys/kernel/security/kacs/sessions`** — lists active logon sessions with session ID, user SID, logon type, and logon time. Requires Administrators or SYSTEM.
