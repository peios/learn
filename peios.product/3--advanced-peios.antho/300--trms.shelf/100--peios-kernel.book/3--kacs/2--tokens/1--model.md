---
title: The Token Model
description: A token is a thread's identity and security policy — how it relates to Linux credentials, primary against effective, and the evaluation context.
---

A token is a kernel object representing a thread's identity and
security policy: the user's SID, group memberships, privileges,
integrity level, impersonation state, claims, confinement settings,
and metadata. Every KACS-mediated access control decision evaluates
the thread's effective token.

Every live userspace thread has one. KACS-mediated authorization never
evaluates a null token — credentials that are blank, uncommitted,
kernel-only, asynchronous, or otherwise outside a meaningful userspace
evaluation context may carry no token at all, and an LSM hook that
reaches KACS with such a credential fails closed rather than evaluate
a meaningless identity.

## Relationship to Linux credentials

Tokens are independently allocated, reference-counted kernel objects.
A `struct cred` holds a *pointer* to the token in its LSM security
blob, not the token data itself.

That indirection is architecturally load-bearing. Linux credentials
are immutable once committed: after `commit_creds()` a `struct cred`
cannot be modified. Had token data been embedded in the credential,
every token mutation — toggling a privilege, adjusting a group — would
have required allocating a whole new credential. Keeping the token
behind a pointer lets token-internal mutations use the token's own
synchronisation and leave the credential alone.

Several thread credentials within a process may reference one token
object through `real_cred`, and a mutation to a shared token is
visible to every thread sharing it. At fork the child receives an
independent deep copy, so mutations after fork are invisible across
the process boundary.

## Primary and effective tokens

The `real_cred`/`cred` split on `task_struct` carries two roles.

`real_cred` is the task's **objective** identity, used when other
tasks evaluate access *to* this task. Its LSM blob points at the
**primary token** — the process's baseline identity, inherited from
the parent at fork.

`cred` is the task's **subjective** identity, used when this task
evaluates access to other objects. Its blob points at the **effective
token**: normally the primary token, or an impersonation token
installed by a server thread acting for a client.

With no impersonation in play, `real_cred` and `cred` are the same
credential and resolve to the same token. Impersonation swaps `cred`
to a new credential pointing at a different token; reverting restores
`cred` to `real_cred`.

## Evaluation context

Token evaluation — AccessCheck, privilege checks — happens only where
a meaningful subject authority exists. In task context that authority
is the effective token reached through `current_cred()`.

Linux credential substitution is authoritative for deferred work. When
a kernel path runs under credentials installed by `override_creds()`
or another subjective-credential mechanism, the token pointer in that
credential's blob travels with it and is evaluated normally. KACS does
not strip authority merely because the current task carries a
kernel-thread, workqueue, or io_uring-worker flag — the credential is
what counts, not the worker flag.

Authorization already cached on an object handle, such as the granted
mask on a file description, continues to use that cached authority for
post-open operations. User-originated asynchronous work that has
neither captured credentials nor cached handle authority reaches KACS
without a token-bearing credential and fails closed.

Kernel-originated infrastructure work running under the boot SYSTEM
credential evaluates as SYSTEM. There is no separate worker-flag-based
kernel authority identity.
