---
title: Credential Projection
type: concept
description: How Peios projects token identity onto Linux UID/GID surfaces, why getuid and current_fsuid can return different numbers during impersonation, and why fsuid is the trustworthy view of effective identity.
related:
  - peios/linux-compatibility/understanding-linux-compatibility
  - peios/identity/how-tokens-work
  - peios/identity/primary-vs-impersonation-tokens
---

Linux applications expect to see numbers. They call `getuid()`, read `/proc/self/status`, look at file owners returned by `stat()`, and use the values they get to make decisions about whether to bind privileged ports, write into a home directory, or drop into an unprivileged sandbox. Peios's identity model is token-based, but unmodified Linux software has no concept of tokens.

**Credential projection** is the bridge. Every token carries a Linux UID and GID that are computed once at token creation time and stamped onto the token. When a token is installed on a thread, the kernel populates the thread's Linux credential structure with the projected values, so any Linux ABI call that reads UIDs or GIDs sees a coherent number derived from the token.

The projected numbers are **observational compatibility data**, not authority. AccessCheck does not consult them. They exist so that Linux applications continue to function — to open the right home directory, to find the right line in `/etc/passwd`, to write log entries with consistent owners — and not because UIDs determine access on Peios.

## How values are projected

When a token is created, authd resolves the principal's `uidNumber` and `gidNumber` attributes from the directory and stamps them onto the token:

- The token's user SID maps to a UID via the directory's `uidNumber` attribute. If the principal has no `uidNumber` set, the UID defaults to **65534** (the conventional `nobody`).
- The token's primary group SID maps to a GID via `gidNumber`, with the same fallback.
- Each group SID in the token that has a `gidNumber` attribute contributes a supplementary GID.

These values are pre-computed; the kernel does not resolve SID-to-UID mappings at runtime. A token always has a projected UID and GID it can hand out without consulting any directory.

`uidNumber` and `gidNumber` are allocated from a **single unified counter** across all principal types. Because SIDs share one namespace but Linux UIDs and GIDs are separate namespaces, every SID projects to a number that is unique regardless of which Linux namespace it lands in. Service A's projected UID is guaranteed not to collide with service B's GID.

Once a token is installed, projected values appear in:

- `getuid()`, `geteuid()`, `getgid()`, `getegid()`, `getgroups()`
- `/proc/<pid>/status` (`Uid:`, `Gid:`, `Groups:` fields)
- File ownership returned by `stat()` for files newly created by this thread
- Audit and accounting records that include UIDs

## Effective token, not primary token

The most important rule of credential projection is this: **projected values reflect the thread's effective token**, not necessarily its primary token.

A thread's effective token is its impersonation token when one is active, and otherwise its primary token. When a service thread calls `kacs_impersonate_*` to act on a client's behalf, the impersonation token becomes the effective token, and the projected credentials follow.

This means a service handling a client request — having impersonated the client — sees:

- File reads and writes attributed to the **client's** UID. Files created by the thread are owned by the client.
- Quotas charged to the **client**, not the service.
- Audit records that name the **client** as the actor.

This matches the Windows access model exactly: during impersonation, the impersonation token governs all operations, including what filesystem credential reads return. After `kacs_revert`, projection returns to the primary token's values.

## `getuid()` versus `current_fsuid()`

Linux exposes two slightly different views of "the current UID", and they deliberately diverge during impersonation:

| Call | What it reads | Behaviour during impersonation |
|---|---|---|
| `getuid()` | The primary credential's UID | Returns the **service's** UID. Unaffected by impersonation. |
| `current_fsuid()` (used by filesystem operations) | The effective credential's UID | Returns the **client's** UID. Tracks impersonation. |

Both are correct, and both are reflecting the truth. `getuid()` answers *"who is this process running as, fundamentally?"* — which is the service. `current_fsuid()` answers *"whose authority does this filesystem operation carry?"* — which during impersonation is the client.

Code that wants to know "is this filesystem operation going to be attributed to me or to someone I'm impersonating right now?" should look at the fsuid surface, not at `getuid()`. Code that wants to know "what fundamental identity is this process running under?" should look at `getuid()`.

## fsuid is locked to the token

Linux's `setfsuid` and `setfsgid` syscalls historically let userspace change filesystem credentials independently of `setuid` — primarily for NFS-server-style per-thread client impersonation. On Peios, this independence does not exist. Filesystem credentials are not a separate piece of state that userspace can edit; they are a **read-through view of the effective token's projected values**.

Specifically:

- `setfsuid(2)` and `setfsgid(2)` cannot meaningfully change the values. The thread's effective token is determined by `kacs_impersonate_*` and `kacs_revert`, and the projected fsuid follows.
- `current_fsuid()` always returns the projected UID of whichever token is currently effective. There is no path by which a thread can run with a fsuid that does not correspond to a real, active token.

This is the key difference between fsuid and uid on Peios: **uid can be made to lie; fsuid cannot.** The next section explains how.

## The `uid0` escape hatch

Some legacy Linux software refuses to function unless `getuid()` returns 0 — package managers, some daemons, init-style tools that originated on systems where root was meaningful. Peios provides a utility, `uid0`, that explicitly overrides `cred->uid` to 0 for the lifetime of a process. With `uid0`, `getuid()` returns 0 even though the underlying token may be a normal service or user token.

The override is **strictly a Linux-credential-field manipulation**. It does not affect KACS:

- The token is unchanged. AccessCheck still evaluates the real token, not "the SYSTEM token."
- `current_fsuid()` continues to return the projected UID from the effective token. uid0 does not flow into the fsuid path.
- Audit attributes the process to the real token's user SID, not to root.

The result is that `getuid()` becomes unreliable as a measure of authority — but `current_fsuid()` does not. This is the practical reason fsuid is the trustworthy view: every projection-affecting compatibility shim has been kept off the fsuid path on purpose, so that anything reading fsuid sees the actual effective token's UID and nothing else.

The uid0 utility is documented in detail on its own page.

## Projection is one-way

State flows from the token into the Linux credential fields, never the reverse:

- `setuid()`, `setgid()`, `setresuid()` and similar calls **succeed cosmetically** — they modify the Linux credential fields the calling process sees — but they do not modify the token. AccessCheck continues to evaluate the original token.
- `AdjustGroups` and other token mutations do not trigger Linux credential recalculation. Projection reflects all groups regardless of enabled/disabled state, computed once at token install time.
- The Linux DAC layer is neutralised (covered in [Understanding Linux Compatibility](understanding-linux-compatibility)) so that DAC's UID-based decisions cannot interfere with the LSM layer where Peios actually enforces.

This one-directional flow is what allows Peios to coexist with Linux-shaped applications without giving the Linux credential surface any security significance. The surface is there to be observed; the token is what is enforced.
