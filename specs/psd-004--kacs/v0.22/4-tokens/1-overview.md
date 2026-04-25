---
title: Token Overview
---

A token is a kernel object representing a thread's identity and security policy. Every thread in Peios MUST have an associated token. There are no NULL tokens.

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

Token evaluation — AccessCheck, privilege checks — MUST only occur when a userspace thread is executing synchronously in the kernel on its own behalf. The token is accessed via `current->cred`, which is only valid in this context.

Kernel threads, workqueues, writeback daemons, io_uring workers, and other asynchronous contexts MUST NOT evaluate tokens from `current->cred` directly. Authorization is evaluated once at the synchronous boundary (e.g., file open), and the result is cached on the object handle (e.g., the granted mask on a file descriptor). Subsequent operations check the cached result.

If a kernel context runs under credentials captured via `override_creds()` (e.g., io_uring, which captures the submitter's credential at submission time), the token pointer in the credential's LSM blob travels with it and MAY be evaluated.

LSM hooks that detect they are running without a meaningful user context (PF_KTHREAD without override, interrupt context) MUST deny rather than evaluate a meaningless identity.
