---
title: Peer credentials
type: concept
description: SO_PEERCRED and SCM_CREDENTIALS return the peer's projected UID/GID — useful for compatibility but insufficient for security decisions. Services that need to authenticate a connecting peer for access control use kacs_open_peer_token instead. This page covers the two Linux mechanisms, their projection semantics, and the right replacement.
related:
  - peios/linux-compatibility/overview
  - peios/linux-compatibility/credential-projection
  - peios/impersonation/peer-tokens
  - peios/tokens/overview
---

When one process connects to another over a Unix socket, the recipient often wants to know who is connecting. Linux provides two mechanisms for this — `SO_PEERCRED` (a socket option) and `SCM_CREDENTIALS` (a control message). Both return basic credential information about the peer.

On Peios, both continue to work and return projected UID/GID values — useful for compatibility with Linux applications, but **insufficient for making security decisions**. For services that need to authenticate the connecting peer's identity to decide access, the right tool is `kacs_open_peer_token`, which returns a full KACS token reflecting the peer's complete identity.

This page covers the two Linux mechanisms and the right replacement.

## SO_PEERCRED

`SO_PEERCRED` is a getsockopt option on a connected Unix socket. The caller queries the socket and gets back a `struct ucred`:

```
struct ucred {
    pid_t pid;
    uid_t uid;
    gid_t gid;
};
```

The fields are:

- `pid` — the connecting peer's PID at connect time.
- `uid` — the projected UID of the peer's effective token at connect time.
- `gid` — the projected GID similarly.

On Peios, the projection is computed from the token at the moment the connection was made. If the peer was impersonating at connect, the projected UID is the impersonated client's. If not, it's the peer's own.

The values are stable for the life of the socket. If the peer changes identity later (impersonation install/revert, token adjustment), the values returned by `SO_PEERCRED` do not update.

### What SO_PEERCRED does not capture

The `struct ucred` is fundamentally lossy. It returns three numbers — pid, uid, gid. It does not return:

- Group memberships beyond the primary GID.
- Privileges.
- Integrity level.
- PIP fields.
- Claims (user or device).
- The session ID.
- Whether the connecting principal is authenticated, anonymous, or somewhere in between.
- The token's restricted-SID list, confinement state, audit policy, or any other non-trivial structure.

For most security purposes, the missing information matters more than what's present. A service that grants access based on UID does not distinguish "user 1001 connecting as their normal Medium-integrity session" from "user 1001 connecting from a Low-integrity sandbox where they shouldn't be doing this". The UID is the same; KACS treats the two cases differently; `SO_PEERCRED` cannot tell them apart.

### What SO_PEERCRED is for

`SO_PEERCRED` is useful for:

- **Logging.** "Connection from PID 12345 (UID 1001) at time T". This is a friendly identification, not a security claim.
- **Display.** A daemon that wants to show "currently connected user: bob" can use the projected UID to look up the name.
- **Coarse compatibility.** Linux applications that already use `SO_PEERCRED` for their own non-security checks continue to work.

For security purposes, it is the wrong tool. The information is too coarse; the connection between projected UID and authoritative identity is too easy to misread.

## SCM_CREDENTIALS

`SCM_CREDENTIALS` is a control message used with `sendmsg`/`recvmsg` on Unix sockets (including datagram sockets where `SO_PEERCRED` doesn't apply). The sender attaches a `struct ucred` to a message; the receiver extracts it.

On Linux, the sender can attach any `struct ucred` they like (subject to capability checks if the values would be different from their actual credentials). Peios projects the same way:

- The sender's projected UID/GID is attached to the message.
- The receiver can extract it via the control-message API.

The same caveats as `SO_PEERCRED` apply: the projected values do not carry the full identity, do not survive non-trivial state changes, and should not be used for security decisions.

`SCM_CREDENTIALS` is the way to attach credential info to datagram messages or `socketpair`-style sockets, where there is no "connect time" to capture peer info at.

## Why these are insufficient for security

The fundamental issue: **the projection is for compatibility, not authority**. UID 1001 corresponds to a SID, and that SID is what KACS uses for access decisions — but the projection doesn't carry the SID. It carries the projected UID, which is a derived value. A service that grants access based on the projected UID is making a decision based on a derivation, not the source of truth.

In practice, this leads to two classes of issue:

**Identity collisions.** Two different principals can in principle project to the same UID. The SID-to-UID mapping is typically 1-to-1, but reasonable failure modes (a misconfigured directory, a colliding mapping during a migration) can produce collisions. KACS sees them as different; UID-based code sees them as the same.

**State that doesn't project.** A token's integrity level, PIP, privileges, restricted-SID status — none of these project to UID/GID. A service that does "if the UID is admin's UID, grant access" cannot tell that the calling process is running on a restricted token with admin's SID but no actual privileges. KACS would deny most accesses; the UID-only check would grant them.

For services that need to be secure, neither `SO_PEERCRED` nor `SCM_CREDENTIALS` is the right tool. The right tool is the KACS-aware peer-token mechanism.

## The replacement: kacs_open_peer_token

`kacs_open_peer_token` is the KACS-native equivalent. The call:

```
token_fd = kacs_open_peer_token(socket_fd)
```

Returns a token fd reflecting the peer's complete identity at connect time. The fd carries `TOKEN_QUERY | TOKEN_IMPERSONATE` access — enough to inspect the token's full state and to install it as an impersonation token.

What the token includes:

- The peer's user SID, group SIDs (with attributes), restricted SIDs, logon SID.
- Their integrity level, mandatory_policy, PIP type and trust.
- Their privileges (present, enabled, used, removed states).
- Their confinement state (sid, capabilities, exempt).
- Their session reference (auth_id).
- Their claims (user and device).
- Their default DACL, owner index, primary group index.
- Their projected UID/GID (for completeness — the same values `SO_PEERCRED` would have returned).

Everything. The full identity, atomic, captured at connect time. From the receiver's perspective, this token is what KACS would have access-decided against if the peer had made the request directly.

The service can:

- **Inspect** the token (via `KACS_IOC_QUERY`) to make authorisation decisions on real identity, not projected UID.
- **Impersonate** the peer (via `KACS_IOC_IMPERSONATE` or `kacs_impersonate_peer`) to perform operations on their behalf — with the just-in-time pattern from [Peer tokens and capture](~peios/impersonation/peer-tokens).

This is the security-grade peer-identity API. For services that need real access control on connecting peers, this is the tool.

## When to use which

A handful of guidelines:

| Want to | Use |
|---|---|
| Log who connected for diagnostic purposes | `SO_PEERCRED` or projected UID-style API |
| Display a "connected as user X" indicator | Same |
| Make an access decision based on peer identity | `kacs_open_peer_token` then KACS-aware logic |
| Act on the peer's behalf (impersonate) | `kacs_impersonate_peer` or `kacs_open_peer_token` + `KACS_IOC_IMPERSONATE` |
| Capture peer identity at connect for later use | `kacs_open_peer_token` (store the fd) |
| Send a credential along a datagram message | `SCM_CREDENTIALS` for compat; for security, pass the token fd via `SCM_RIGHTS` |

The pattern: compatibility-grade peer ID uses the Linux APIs; security-grade peer ID uses the KACS APIs. The distinction matters most for services that handle untrusted callers — a public-facing daemon should use `kacs_open_peer_token`; an internal diagnostic tool can use `SO_PEERCRED`.

## What about TCP sockets

Linux's `SO_PEERCRED` does not work on TCP sockets — the peer is potentially remote, and there's no kernel-side credential to query. The same is true on Peios: KACS does not capture peer tokens over TCP. The peer is whatever the network layer says it is, identified by IP / connection state, not by a token.

For services accepting TCP connections from authenticated peers, the authentication is at a different layer — TLS with mutual certificates, Kerberos via authd, application-layer protocols. The result of that authentication is what determines the connecting principal's identity; the kernel-level peer-credential APIs are not involved.

Once authentication has produced a token (typically by authd), the service can install that token as an impersonation token via the normal `KACS_IOC_IMPERSONATE` path. The token-installation API is uniform regardless of whether the token came from a Unix-socket peer or a TCP-authenticated session.

## What goes wrong if you use the wrong tool

A few concrete failure modes from using `SO_PEERCRED` for security:

- **Sandbox bypass.** A user runs a sandboxed application that connects to a privileged daemon. The application's token has the user's SID (restricted, with privileges removed). The daemon does `SO_PEERCRED`, sees UID 1001, looks the user up, sees they're in the administrators group, grants admin access. The sandbox is bypassed — KACS would have refused based on the restricted token, but the daemon never asked KACS.
- **Impersonation confusion.** A service that connects to another service while impersonating a client should appear (to the receiver) as the client. With `SO_PEERCRED`, the receiver sees the client's projected UID — correct in this case. But if the impersonation changed mid-session (the service reverted, then made another call), `SO_PEERCRED` still shows the original peer's UID. The receiver can be confused about who they're actually serving.
- **Identity not present in projection.** A service that wants to make decisions based on the peer's integrity level cannot — there's no projection for it. A `SO_PEERCRED`-using service sees nothing about integrity; the call effectively ignores that axis of access control.

For each of these, `kacs_open_peer_token` would produce the correct result because the token carries the full identity. The migration path for an existing service is: replace `SO_PEERCRED` calls with `kacs_open_peer_token`, use the token to make decisions instead of the projected UID. The code surface changes; the semantic is more accurate.

## Compatibility, not removal

`SO_PEERCRED` and `SCM_CREDENTIALS` are not being removed. They continue to work with sensible semantics for compatibility with Linux software. The recommendation is to migrate security-sensitive code to KACS-aware APIs, not to deprecate the Linux APIs.

For most services this means: keep the Linux API for friendly identification; add KACS-aware logic for access decisions. Both can coexist on the same connection; the security paths use the KACS-aware data, the diagnostic paths use the Linux API.
