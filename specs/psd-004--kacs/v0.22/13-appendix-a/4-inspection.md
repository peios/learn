---
title: Inspection Interfaces
---

## procfs

**`/proc/<pid>/token`** — displays the primary token of process `<pid>`. Gated by PROCESS_QUERY_INFORMATION on the target process's SD, plus PIP dominance check for protected processes. Reading `/proc/self/token` is always allowed.

**`/proc/<pid>/task/<tid>/token`** — displays the effective token of thread `<tid>`. Shows the impersonated token if the thread is impersonating. Same access requirements as `/proc/<pid>/token` (PROCESS_QUERY_INFORMATION + PIP dominance).

## securityfs

**`/sys/kernel/security/kacs/self`** — the calling thread's effective token. Protected by an SD granting Everyone FILE_READ_DATA. Always readable.

**`/sys/kernel/security/kacs/sessions`** — lists active LogonSessions with LogonSession ID, user SID, logon type, auth package, and logon time. Protected by an SD granting BUILTIN\Administrators and SYSTEM FILE_READ_DATA. Access is enforced via normal AccessCheck against this SD — no special privilege check.
