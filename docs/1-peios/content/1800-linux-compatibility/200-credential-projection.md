---
title: Credential projection
type: concept
description: The token's identity is projected into the Linux UID/GID fields, computed once from the directory's SID-to-UID mapping and cached on the token. Standard Linux syscalls return these projected values; the kernel never trusts them as authoritative. This page covers the projection mechanism, how impersonation affects what Linux APIs see, and the rule that no Linux API writes back to the token.
related:
  - peios/linux-compatibility/overview
  - peios/linux-compatibility/dac-neutralization-and-capabilities
  - peios/linux-compatibility/setuid-and-uid0
  - peios/tokens/overview
  - peios/identity/overview
---

The projection model is straightforward: when authd mints a token, it resolves the user's SID against the directory's SID-to-UID mapping and stores the resulting UID, GID, and supplementary GIDs on the token. These values are the *projection* — derived from the SID, not parallel to it. From then on, any Linux API that asks "what's this process's UID?" gets the answer from the projection.

The projection is one-way. Token state determines the projection; the projection never determines token state. There is no API that lets a Linux call modify the token through the projection layer; the token is authoritative.

This page covers how the projection is constructed, what Linux APIs see when they consult it, how impersonation changes the visible projection, and the rule that keeps the model consistent.

## What's on the token

Every token carries three projection-related fields:

| Field | Meaning |
|---|---|
| `projected_uid` | The Linux UID corresponding to the token's user SID. `65534` if the SID has no mapping. |
| `projected_gid` | The Linux GID corresponding to the token's primary group SID. Same fallback. |
| `projected_supplementary_gids` | An array of GIDs for the supplementary groups on the token. |

These fields are set when the token is created. authd reads the user's SID-to-UID mapping from the directory at authentication time, fills in the projection, and includes the values in the wire-format token specification passed to `kacs_create_token`.

The mapping is per-directory. On a standalone Peios system, loregd's registry holds the mapping; on a domain-joined system, AD provides it. The same SID can in principle map to different UIDs on different systems if the directories are different, though in practice deployments aim for consistency.

A SID with no mapping (a principal that exists in the directory but has no UID assignment) projects to `65534` — the conventional Linux "nobody" UID. This lets the projection produce a value even when the directory does not have one, while signalling that the principal is unknown to the projection.

## What syscalls see

The standard Linux identity syscalls all return projected values:

| Syscall | Returns |
|---|---|
| `getuid()` | The primary token's `projected_uid`. |
| `geteuid()` | The effective token's `projected_uid` — primary if not impersonating, impersonation token's value if impersonating. |
| `getgid()` | The primary token's `projected_gid`. |
| `getegid()` | The effective token's `projected_gid`. |
| `getresuid(&r, &e, &s)` | Same: `r` and `s` from primary, `e` from effective. |
| `getresgid(&r, &e, &s)` | Same. |
| `getgroups()` | The effective token's `projected_supplementary_gids`. |
| `getlogin()` (via libc) | Reads `/proc/self/status` which reads the primary token's projection. |
| `stat()`, `fstat()`, `lstat()` | File's owner SID projected to UID, primary group SID projected to GID. |
| `/proc/<pid>/status` | The primary and effective token's projected fields. |
| `/proc/<pid>/loginuid` | The primary token's projected UID. |

The split between `getuid` (primary) and `geteuid` (effective) preserves Linux semantics where the two diverge during impersonation-like operations. On Peios, the divergence is when the thread is actually impersonating.

The kernel maintains the synchronisation between token state and these queries automatically. Adjusting privileges, adjusting groups, installing/reverting impersonation — each updates whatever the next `getuid()`-style call would see.

## What impersonation does

A thread that is currently impersonating has two tokens: its primary and its impersonation. The projection layer follows the **effective** token (the impersonation, while it's in effect) for `geteuid`-style queries and the primary for `getuid`-style queries.

The result:

- Before impersonating: `getuid() == geteuid() == projected_uid(primary)`.
- During impersonation: `getuid() == projected_uid(primary)`, `geteuid() == projected_uid(impersonation)`.
- After reverting: back to the first state.

A program checking "am I running as user X right now?" via `geteuid()` sees the impersonated user, not the service's own user. A program checking "what's my real identity?" via `getuid()` sees the service's own user.

This is the standard Linux divergence: real (primary) vs effective (current). Peios preserves it through the projection. A service that captures a client's identity via impersonation and then opens a file as the client sees the file open with the client's projection (which is what allows the open to succeed if the client has access); other Linux calls on the same thread see the same effective identity.

The threads that are not impersonating see only the primary projection. Impersonation is per-thread; the projection is too.

## current_fsuid() and the fsuid path

A subtle case: the Linux kernel internally uses a function called `current_fsuid()` (and the corresponding `current_fsgid()`) for file-related credential lookups — file ownership, disk quotas, keyring lookups, NFS credentials. These are different from `getuid()`/`geteuid()`; they go through their own code path inside the kernel.

Peios **patches** `current_fsuid()` (and its variants) to return the projected UID from the **effective** token, not from `cred->fsuid`. This is what makes the projection consistent across all the places the kernel might consult it.

The practical effect: a thread impersonating a client opens a file. The Linux kernel might internally call `current_fsuid()` to record who created the file in the filesystem's metadata. The patched `current_fsuid()` returns the impersonated client's UID, so the file appears to be created by the client. This is consistent with the file's owner SID being the client's SID (which KACS would set), and consistent with `stat()` later returning the client's UID.

Without the patch, `current_fsuid()` would return `cred->fsuid`, which might be the service's own UID — and the file's metadata would be inconsistent with the file's actual KACS owner.

## The one-way rule

**The projection flows token → cred. Never cred → token.**

A Linux call that would, on a non-Peios system, modify the kernel's notion of the process's UID is **not** allowed to modify the token. Specifically:

- `setuid()` and friends do not modify the token. They either become a no-op (without `SeAssignPrimaryTokenPrivilege`) or trigger a full identity swap through authd (with the privilege). See [setuid and uid0](~peios/linux-compatibility/setuid-and-uid0).
- The setuid-on-exec bit (`S_ISUID` in a file's mode) similarly does not modify the token without the privilege.
- `prctl(PR_SET_SECUREBITS)` and related operations do not affect the token's projection.

The reason: the token is the authoritative identity. Letting Linux APIs write to it would mean the token's value depends on what Linux code thinks. Peios's model is that the token is decided by authd (at mint time) and adjusted only through KACS APIs (AdjustPrivileges, AdjustGroups, etc.). Linux is a consumer; it does not get to be a producer.

## File ownership in stat()

When `stat()` returns a file's owner and group, the values come from the file's SD — specifically, the owner SID's projection and the primary group SID's projection.

The flow:

1. The file has an SD with `owner_sid = S-1-5-21-...-1001` and `group_sid = S-1-5-21-...-513`.
2. Each SID is run through the SID-to-UID mapping.
3. `stat()` returns `st_uid = 1001`, `st_gid = 513`.

The values are computed from the SD's SIDs every time, not stored as separate fields. The file's underlying filesystem may have its own `i_uid` and `i_gid` fields (ext4 does), but the kernel maintains them consistent with the SD-derived values. A change to the file's owner SID via `kacs_set_sd` updates the SD and re-derives the projected UIDs, which then become visible to `stat()`.

This consistency is what makes `ls -l` work. The output shows ownership; the ownership is the projection of the SD; the SD is what KACS evaluates against. The three views agree.

## SO_PEERCRED and SCM_CREDENTIALS

Two Linux APIs let one process learn another's identity over Unix sockets:

- **`SO_PEERCRED`** — getsockopt option returning the peer's `pid`, `uid`, `gid`.
- **`SCM_CREDENTIALS`** — sendmsg/recvmsg control message allowing the sender to attach (or the receiver to extract) similar credentials.

On Peios, these return the peer's projected UID/GID values. The values are correct in the projection sense — they correspond to the peer's token's projection. But they are **not** the right tool for security-relevant identity:

- They don't distinguish between an authenticated user and an unauthenticated process running as the same UID.
- They don't carry the token's SIDs, groups, integrity level, or privileges.
- They don't reflect impersonation correctly in all cases.

For security purposes, the right tool is `kacs_open_peer_token` — it returns a token fd carrying the full identity. See [Peer credentials](~peios/linux-compatibility/peer-credentials).

`SO_PEERCRED` and `SCM_CREDENTIALS` are kept for compatibility with Linux applications that use them for non-security purposes (logging, debugging, friendly identification). Code that needs to make access decisions on peer identity uses the KACS-aware API.

## What the projection is *not*

A few clarifications:

- **The projection is not the access decision input.** KACS uses the token (SIDs, groups, privileges, integrity, PIP); the projection is for Linux API compatibility only. AccessCheck does not consult `projected_uid`.
- **The projection is not historical.** A token reflects identity now; if the SID-to-UID mapping changes (rare but possible), existing tokens continue to use their cached projection. New tokens (created after the mapping change) would see the new value. The projection is fixed when the token is minted.
- **The projection is not the file system's notion of ownership.** ext4 stores `i_uid` and `i_gid`; Peios keeps these consistent with the SD's owner-projection, but the SD is authoritative. A file whose `i_uid` somehow diverges from the SD owner's projection is inconsistent; KACS uses the SD.
- **The projection is not a substitute for the token.** Code that needs to make security decisions on identity should use the token, not the projection. The projection is for compatibility; the token is for authority.

The cleanest mental model: the projection is the *Linux-shaped view* of an identity that fundamentally lives in KACS. It exists to satisfy POSIX programs that ask "what's my UID?" and have to get a number back. The number is computed; the actual identity is something else.
