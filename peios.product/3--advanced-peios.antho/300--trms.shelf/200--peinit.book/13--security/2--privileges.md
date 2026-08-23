---
title: peinit's Privileges
description: peinit runs as SYSTEM with every privilege, and the much narrower set it actually exercises.
---

peinit runs as SYSTEM with every privilege for the lifetime of the
system. What it actually exercises is narrower.

| Privilege or capability | Used for |
|---|---|
| `SeCreateTokenPrivilege` | Minting SYSTEM tokens for platform services during bootstrap, before authd exists (§4.2). |
| `SeTcbPrivilege` | Requesting tokens from authd on a service's behalf, and installing a primary token on a child whose identity differs from peinit's own. |
| Process creation | Fork and exec, inherent to PID 1. |
| cgroup management | Creating and destroying trees under `/sys/fs/cgroup/peinit/`. |
| Signal delivery | SIGTERM and SIGKILL to managed processes. |
| Mount operations | The Phase 1 virtual filesystems. |

peinit does not verify at startup that it holds any of these. A missing
`SeCreateTokenPrivilege` surfaces as an `EPERM` from the first token
mint, which is the first service start.

`SeImpersonatePrivilege` is not used. peinit passes the peer's token
descriptor to AccessCheck directly rather than impersonating the caller
and evaluating as them, so the privilege that would be needed to
impersonate is not needed at all.

For non-platform services peinit creates no tokens. It installs the ones
authd minted. It mints only for the SYSTEM platform services it starts
during bootstrap, before authd is available.

> [!NOTE]
> Minting is interim. The intended model derives a service's token from
> peinit's own handle through a KACS duplicate-with-additions operation
> — kernel-attested as a descendant of peinit's real token, and needing
> no minting privilege. That would let peinit drop
> `SeCreateTokenPrivilege` entirely, which is the point: the privilege
> to mint arbitrary tokens is the strongest thing peinit holds and the
> one it has the least use for.
