---
title: Bootstrap tokens
type: concept
description: Before any userspace process exists, the kernel directly constructs two tokens — SYSTEM and Anonymous — that bootstrap the identity model. SYSTEM is authority-maximal and runs init; Anonymous is identity-minimal and backs Anonymous-level impersonation. This page covers what each carries, how they're constructed without going through kacs_create_token, and why they persist for the kernel's lifetime.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/tokens/overview
  - peios/tokens/lifecycle
  - peios/identity/well-known-principals
---

The kernel constructs two tokens directly during initialisation, before any userspace process exists. These are the **SYSTEM token** and the **Anonymous token**. Both exist as singletons in the kernel from the moment kernel init completes; both persist for the lifetime of the running kernel; both are created without going through `kacs_create_token` (there is no userspace caller to make that syscall).

The two tokens have opposite roles. SYSTEM is the authority-maximal token — every privilege, every well-known administrative group, integrity System — that gets attached to init and bootstraps every other userspace token. Anonymous is the identity-minimal token — no real principal, no privileges, integrity Untrusted — that backs the Anonymous-level of impersonation.

This page covers what each contains and why they're constructed this way.

## SYSTEM — authority-maximal bootstrap

The SYSTEM token is what init runs on. Specifically:

| Field | Value |
|---|---|
| `user_sid` | `S-1-5-18` (the SYSTEM well-known SID) |
| `groups` | `BUILTIN\Administrators` (with `SE_GROUP_OWNER`), `Everyone`, `Authenticated Users`, `Local`, and the bootstrap logon SID `S-1-5-5-0-0` |
| `integrity_level` | `S-1-16-16384` (System integrity — the highest) |
| `mandatory_policy` | `NO_WRITE_UP` |
| `privileges` | Every privilege defined in the catalog, all present, all enabled |
| `token_type` | Primary |
| `impersonation_level` | Anonymous (conventional for primary tokens) |
| `auth_id` | 0 (the SYSTEM session) |
| `default_dacl` | Grants SYSTEM and `BUILTIN\Administrators` `GENERIC_ALL`; denies everyone else by absence |

The SYSTEM token is *the* most powerful identity on a running Peios system. It has every privilege, full administrative-group membership, the highest integrity. The only thing it lacks is a specific real principal — it's a system-internal identity, not a user.

The SYSTEM token has session ID 0, which corresponds to the SYSTEM session (also kernel-constructed). The session is a peer of the token; both exist together from kernel init.

The default DACL on the SYSTEM token is restrictive in an important way: when SYSTEM creates a new object without specifying an explicit SD, the default DACL ends up on the object. Granting only SYSTEM and Administrators means objects SYSTEM creates are administrator-only by default. This is the right policy for things like service configuration files — they should not be readable by every user just because they were created during boot.

## Anonymous — identity-minimal singleton

The Anonymous token has the opposite shape. It's not used for running processes; it's used as the **identity** of Anonymous-level impersonation tokens (the lowest impersonation level — see [Impersonation levels](~peios/impersonation/impersonation-levels)).

| Field | Value |
|---|---|
| `user_sid` | `S-1-5-7` (the Anonymous well-known SID) |
| `groups` | `Everyone` only |
| `integrity_level` | `S-1-16-0` (Untrusted — the lowest) |
| `mandatory_policy` | `NO_WRITE_UP` |
| `privileges` | None |
| `token_type` | Impersonation (it exists specifically for impersonation) |
| `impersonation_level` | Anonymous |
| `auth_id` | 998 (the Anonymous session) |

The Anonymous token has the bare minimum to be a token at all. No real principal (the user SID is the well-known "Anonymous" placeholder). Just `Everyone` for groups — explicitly **not** `Authenticated Users`. No privileges. Untrusted integrity.

When a client connects to a server and sets the impersonation level to Anonymous (or the gates downgrade the impersonation level to Anonymous), the server's effective token becomes a derivation of this Anonymous token — essentially a copy with the relevant session bindings. The kernel's "Anonymous identity" is centrally defined here; the rest of the system inherits from it.

## Why kernel-direct construction

The two tokens are constructed by direct kernel initialisation, **not** via `kacs_create_token`. This matters because `kacs_create_token` requires `SeCreateTokenPrivilege` — which requires a caller — which requires a token — which is exactly what's being established. The bootstrap problem.

The kernel breaks the cycle by constructing these two tokens with internal code that doesn't go through the usual API. The kernel can do this because it is the kernel; there's no privilege check on itself.

The implications:

- **No record exists of who minted these tokens.** The `source` field, normally set to whatever component called `kacs_create_token`, is set by the kernel to indicate "kernel-internal". The tokens were not minted by authd, peinit, or any other component.
- **They cannot be re-created at runtime.** Even though both tokens have the same shape every time they're constructed (the values are kernel-internal constants), no userspace component can ask the kernel to construct another SYSTEM token at the same level. SeCreateTokenPrivilege lets userspace create *new* tokens; it doesn't grant access to construct kernel-internal singletons.
- **They are singletons.** There is exactly one SYSTEM token and one Anonymous token at any moment in the kernel. Other tokens may reference them or be derived from them, but the canonical instances are unique.

The kernel-direct construction is the foundation: it gives the rest of the system a starting identity to build from. Once SYSTEM exists and is attached to init, everything that follows can use normal API calls — they have a token, they have privileges, they can mint other tokens.

## What's attached to what

At the end of kernel init:

- **SYSTEM token.** Constructed; ready.
- **Anonymous token.** Constructed; ready.
- **SYSTEM session (ID 0).** Constructed; the SYSTEM token is bound to it.
- **Anonymous session (ID 998).** Constructed; the Anonymous token is bound to it.
- **init process.** About to start; will have the SYSTEM token attached to it.

Init starts and takes the SYSTEM token as its primary token. The first userspace process the kernel runs is **prelude**, the PID 1 of the initramfs — the in-memory startup environment that mounts the real root (see [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage)). The SYSTEM token survives every exec along the way: prelude runs on it, and when prelude hands the machine to the real root it execs **peinit**, which takes over with the SYSTEM token as its own.

From this point on, the only entity with the SYSTEM token is peinit (and anything peinit chooses to fork before assigning each child its own token). When peinit launches authd, it does so by forking and then either letting the child inherit SYSTEM (briefly, until authd starts assigning a different token to itself) or by replacing the token with one peinit prepared.

The Anonymous token is not attached to any process. It exists as a kernel-internal object; impersonation tokens at the Anonymous level are derivations of it but the canonical instance lives in the kernel.

## Lifecycle

Both bootstrap tokens are **never destroyed during the kernel's lifetime**. They are reference-counted like any other tokens, but their references never drop to zero because:

- The SYSTEM token has at least one attachment (initially init, then peinit, then whatever process inherits from peinit). Even after peinit assigns specific tokens to most child processes, peinit itself continues to run on SYSTEM.
- The Anonymous token is a kernel-internal singleton. The kernel holds a reference to it; the reference is not dropped until kernel shutdown.

On reboot, the kernel re-constructs them at init. They are not persistent — there is no on-disk SYSTEM-token record — they are re-built fresh every boot. The fields are deterministic, so the new instances are equivalent to the previous ones structurally; the actual token instances are different objects.

The session IDs (0 for SYSTEM, 998 for Anonymous) are also fixed across boots. The logon SID derived from the SYSTEM session is `S-1-5-5-0-0`.

## Why these specific shapes

The SYSTEM token has every privilege and full administrative-group membership because it needs to be able to do anything. Boot involves operations that require a wide range of privileges — `SeLoadDriverPrivilege` to load kernel modules, `SeBackupPrivilege` / `SeRestorePrivilege` for early-system manipulation, `SeShutdownPrivilege` for orderly shutdown. Restricting SYSTEM would force peinit to know in advance which privileges it would need, which is brittle.

`SeBackupPrivilege` and `SeRestorePrivilege` are special — they're on the SYSTEM token at boot, but peinit typically calls FilterToken to **remove** them when assigning tokens to services that don't need them. SYSTEM having them is the starting point; the actual services usually run without them.

The Anonymous token has the opposite design: nothing it shouldn't need. The Anonymous identity is what gets used when a caller has not authenticated, and granting it any group beyond `Everyone` would risk accidentally giving anonymous callers access to resources whose DACLs name those groups. Empty privileges, Untrusted integrity, no `Authenticated Users` membership.

The two tokens together establish the trust range. SYSTEM is "the most trust the system can confer"; Anonymous is "the least trust meaningful". Every other token sits somewhere between, with parameters set by authd from the directory.

## What the bootstrap tokens are not

A few clarifications:

- **They are not user accounts.** SYSTEM is the system's own identity; Anonymous is the placeholder for "no identity". Neither corresponds to a user that signed in.
- **They are not interchangeable with administrator tokens.** A real user in the `BUILTIN\Administrators` group has a different token from SYSTEM — same group membership conceptually, but with the user's actual user_sid, the user's session, etc. SYSTEM and Administrators are not the same identity.
- **They don't persist across reboots.** Every boot constructs fresh instances. Anything keyed to the SYSTEM token's instance ID (which is rare; nothing should be) would lose its reference at reboot.
- **They cannot be modified.** Almost everything about them is immutable. AdjustPrivileges would technically be possible on SYSTEM (a token holder of SYSTEM could enable/disable privileges, or even remove them) but the kernel makes such adjustments a one-time event for the bootstrap token, and the field-level operations are constrained. In practice nothing modifies the SYSTEM token directly; peinit makes filtered copies for child tokens.
