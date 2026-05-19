---
title: Token Overview
---

A token is a kernel object representing a thread's identity and security
policy. Every live userspace thread in Peios MUST have an associated token for
KACS-mediated authorization. KACS-mediated userspace authorization MUST NOT
evaluate a NULL token.

Credentials that are blank, not yet committed, kernel-only, asynchronous, or
otherwise outside a meaningful userspace evaluation context MAY carry no token.
If such credentials reach an LSM hook that would otherwise evaluate KACS policy,
the hook MUST fail closed rather than evaluate a meaningless identity.

A token carries: the user's identity (SID), group memberships, privileges, integrity level, impersonation state, claims, confinement settings, and metadata. All KACS-mediated access control decisions evaluate the thread's effective token.

## Credential relationship

Tokens exist as independently allocated, reference-counted kernel objects. The Linux credential structure (`struct cred`) holds a pointer to the token in its LSM security blob — not the token data itself.

This separation is architecturally significant. Linux credentials are immutable once committed — after `commit_creds()`, a `struct cred` cannot be modified. If token data were embedded in the credential, every token mutation (toggling a privilege, adjusting groups) would require allocating a new credential. By keeping the token as an independent object behind a pointer, token-internal mutations use the token's own synchronization and do not require credential reallocation.

Within a process, multiple thread credentials MAY reference the same token object (via `real_cred`). Mutations to a shared token (privilege enable/disable, group adjustment) are visible to all threads sharing that token. At fork, the child MUST receive an independent deep copy of the parent's token — mutations after fork are invisible across the process boundary.

## Primary and impersonation tokens

The credential carries two roles via the `real_cred`/`cred` split on `task_struct`:

- **`real_cred`** — the task's objective identity. Used when other tasks evaluate access *to* this task. Its LSM blob holds a pointer to the **primary token**: the process's baseline identity, inherited from the parent on fork.

- **`cred`** — the task's subjective identity. Used when this task evaluates access *to other objects*. Its LSM blob holds a pointer to the **effective token**: either the primary token (the common case) or an impersonation token installed by a server thread acting on behalf of a client.

In the common case (no impersonation), `real_cred` and `cred` point to the same `struct cred`, and both resolve to the same token object. Impersonation swaps `cred` to a new credential whose LSM blob points to a different token. Reverting restores `cred` to `real_cred`.

## Evaluation context

Token evaluation — AccessCheck, privilege checks — MUST only occur when a meaningful subject authority is available. In task context, the subject authority is the effective token reached through the task's subjective credential, `current_cred()` / `current->cred`.

Linux credential substitution is authoritative for deferred work. If a kernel path runs under credentials installed by `override_creds()` or another Linux subjective-credential mechanism, the token pointer in that credential's LSM blob travels with it and MAY be evaluated. KACS MUST NOT strip authority merely because the current task has a kernel-thread, workqueue, io_uring-worker, or similar worker flag.

Authorization already cached on an object handle (for example, the granted mask on a file description) continues to use that cached authority for post-open operations. User-originated asynchronous work that lacks both captured credentials and cached handle authority MUST fail closed by reaching KACS without a meaningful token-bearing credential.

If no token-bearing subjective credential is available for a KACS-mediated authorization decision, the hook MUST fail closed rather than evaluate a meaningless or NULL identity. Kernel-originated infrastructure work running under the boot SYSTEM credential is evaluated as SYSTEM; KACS does not define a separate worker-flag-based kernel-authority identity.
