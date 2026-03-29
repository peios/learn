---
title: PSB Overview
order: 1
---

The Process Security Block (PSB) is a per-process security structure that carries properties describing **what the process is** -- determined by the binary that was loaded, not by the principal running it.

The PSB is separate from the token. The token describes identity and travels with impersonation -- when a thread impersonates a client, the effective token changes. The PSB describes the process and MUST NOT be affected by impersonation. This is the load-bearing invariant:

> The PSB is never affected by impersonation. Impersonation changes who the thread is acting as. It does not change what the process is.

The PSB lives on the task's LSM security blob (`task_struct->security`), separate from the credential which holds the token pointer. The credential is swapped during impersonation; the PSB is not.
