---
title: Peer Credentials
type: concept
description: Peer authentication on Unix sockets — the SO_PEERCRED family, the new SO_PEERTOKEN and SO_PEERGUID, and the recommended Peios authentication patterns.
related:
  - peios/IPC/unix-domain-sockets
  - peios/IPC/fd-passing
  - peios/identity/primary-vs-impersonation-tokens
  - peios/linux-compatibility/credential-projection
---

A server accepting a Unix-socket connection usually wants to know *who* connected. Linux has a small family of socket options and ancillary message types for this; Peios extends it with KACS-native primitives. This page covers the full surface and the recommended patterns.

The fundamental property: **all peer-credential primitives are kernel-attested.** The peer cannot lie about the values returned, because the kernel reads its own credentials of the peer and writes them in. This is what makes peer authentication via Unix sockets meaningful — the server gets ground-truth identity, not whatever the peer claims.

## The Linux primitives

Five Linux primitives, each with different semantics and use cases:

| Primitive | Surface | When values captured | What it returns |
|---|---|---|---|
| `SO_PEERCRED` | `getsockopt` | Connect time | PID, UID, GID of peer. |
| `SCM_CREDENTIALS` | `recvmsg` ancillary | Per message at send time | PID, UID, GID of sender. Requires `SO_PASSCRED` on the receiving socket. |
| `SO_PEERSEC` | `getsockopt` | Connect time | Peer's security context as a string. |
| `SCM_SECURITY` | `recvmsg` ancillary | Per message | Sender's security context. Requires `SO_PASSSEC`. |
| `SO_PEERPIDFD` | `getsockopt` | Connect time | Pidfd of peer (kernel 6.5+). Race-free vs PID reuse. |

`SO_PEERCRED` and `SO_PEERSEC` are connection-scoped — captured once at connect time and frozen for the connection's lifetime. `SCM_CREDENTIALS` and `SCM_SECURITY` are per-message — each `recvmsg` may receive new credential information reflecting the sender at send time.

The historical Linux pattern is to use `SO_PEERCRED.uid` for authentication: "is this connection from UID 0?" works on Linux because UID is a real security identity there. On Peios, UIDs are projection artefacts with no security meaning, so this pattern needs adaptation.

## Peios-specific behaviour

Peios honours the Linux ABI for these primitives but adapts the values returned to fit the KACS identity model.

### SO_PEERCRED and SCM_CREDENTIALS

These primitives return projected UID/GID values **truth-projected from the peer's effective token at capture time** — the same projection mechanism that drives `current_fsuid()`. A thread connecting to a server while impersonating produces an SO_PEERCRED on the server side reflecting the impersonated identity.

| Field | Source on Peios |
|---|---|
| `pid` | Peer's PID at capture time. |
| `uid` | Projected UID of peer's effective token at capture. |
| `gid` | Projected primary group GID of peer's effective token at capture. |

Linux software that does `if (peer.uid == 0) allow_admin()` produces a meaningful answer on Peios because the projection is deterministic from the peer's token. UID 0 (or whatever number SYSTEM projects to in the active mapping) reliably indicates a SYSTEM-tier peer.

**Important caveat:** even with truth-projection, UIDs are lossy. Multiple distinct KACS principals can project to the same UID; the projection mapping can change. UID-based checks are usable as a quick gate, but **authentication-bearing decisions should use Peios-native primitives** (below). UID checks are the analogue of comparing fingerprints by colour — fast, mostly right, but the fundamental identity surface is the SID, not the projected number.

The Peios extension does not require `SO_PASSCRED` to be set explicitly on every socket — the kernel always populates the values truthfully. The Linux flag exists for ABI compatibility but is effectively a no-op on Peios (the values are always available regardless).

### SO_PEERSEC and SCM_SECURITY

The Linux semantics carry the peer's SELinux security context. SELinux does not exist on Peios, so these primitives are repurposed to return **the peer's user SID as an SDDL string** — the standard Microsoft string form, e.g. `S-1-5-18` for SYSTEM, `S-1-5-21-…-1001` for a domain user.

The string is suitable for log lines, audit records, and any code that wants to display or compare the peer's security identity in a stable, parseable form. SDDL has a fixed grammar; standard tooling (Windows interop libraries, the Peios SDDL parsers) can interpret it without bespoke code.

### SO_PEERPIDFD

Substrate-as-is. Returns a pidfd referring to the peer process at connect time. The pidfd is stable across PID reuse — even if the peer exits and a new process inherits its PID, the pidfd does not refer to the new process; it tracks the original or returns "exited" status if queried.

`SO_PEERPIDFD` is the recommended Peios-native handle for "give me a stable reference to the peer process." Combined with the standard pidfd-introspection mechanisms (process-SD-gated reads of the process's primary token, queries about process state, etc.), it provides a complete cross-process identity-and-state inquiry surface.

## Peios-native primitives

Two Peios-native socket options provide direct KACS-level peer information.

### SO_PEERTOKEN

`getsockopt(sockfd, SOL_SOCKET, SO_PEERTOKEN, &tokfd, &len)` returns a **token file descriptor** — a kernel handle to a freshly-derived impersonation-class token from the peer's effective token at connect time.

The userspace flow:

```c
int tokfd;
socklen_t len = sizeof(tokfd);
getsockopt(connfd, SOL_SOCKET, SO_PEERTOKEN, &tokfd, &len);
kacs_impersonate_token(tokfd);
/* ... operations now run as the peer ... */
kacs_revert();
close(tokfd);
```

The kernel handler:

1. Verifies the calling process has authority to impersonate the peer — the peer's process SD must permit this, and PIP dominance must hold.
2. Constructs an impersonation-class duplicate of the peer's effective token.
3. Allocates a fresh fd in the caller's fd table referencing that token.
4. Writes the fd number into `optval`.

`SO_PEERTOKEN` is the "authenticate by impersonation" primitive that matches the Windows model. A server accepts a connection, retrieves an impersonation token for the peer, runs the requested operation under that token via `kacs_impersonate_token`, and the kernel's normal AccessCheck path decides whether the operation is permitted. The server doesn't have to think about authorisation logic; the kernel does it under the right identity.

`SO_PEERTOKEN` replaces the previously-separate `kacs_get_peer_token` syscall — peer-token retrieval is consolidated into the standard `getsockopt` discovery surface.

### SO_PEERGUID

`getsockopt(sockfd, SOL_SOCKET, SO_PEERGUID, &guid, &len)` with `len = 16` returns the peer's **process GUID** — the kernel-generated UUID that identifies a process for its lifetime and beyond (for audit purposes, GUIDs do not recycle when a process exits).

Process GUIDs are useful for stable-identity logging, deduplication across reconnects (was this the same peer process?), and any "have I seen this peer before" question that PID can't reliably answer because of reuse. Unlike `SO_PEERTOKEN`, retrieving the GUID does not allocate any kernel handle and does not require the peer's process SD to permit anything — possessing the connection is enough.

## The recommended patterns

Three patterns cover the common authentication needs.

### Quick gate via SO_PEERCRED

For a fast initial check (e.g. "this socket only handles connections from system services"), `SO_PEERCRED` is the minimum-friction option. The truth-projected UID is reliable enough for gross-categorisation decisions:

```c
struct ucred peer;
socklen_t len = sizeof(peer);
getsockopt(sockfd, SOL_SOCKET, SO_PEERCRED, &peer, &len);

if (peer.uid != 0) {
    /* not SYSTEM-tier — refuse */
    close(sockfd);
    return;
}
```

This is good enough for many operational gates. It is not an authoritative authentication; for that, escalate to `SO_PEERTOKEN` or `SO_PEERSEC`.

### Authoritative auth via SO_PEERSEC

When the server wants to verify the peer is a specific KACS principal, retrieve the SDDL string and compare:

```c
char sid[128];
socklen_t len = sizeof(sid);
getsockopt(sockfd, SOL_SOCKET, SO_PEERSEC, sid, &len);

if (strcmp(sid, "S-1-5-18") != 0) {  /* SYSTEM */
    refuse_connection();
}
```

This is authoritative because the SID is the actual security identity, not a projection. Two peers with different SIDs but the same projected UID will produce different SO_PEERSEC values.

### Authentication by impersonation via SO_PEERTOKEN

For servers that perform operations on behalf of clients (the classic file-server pattern), retrieve the peer's token and impersonate. The kernel's AccessCheck handles authorisation:

```c
int tokfd;
socklen_t len = sizeof(tokfd);
getsockopt(connfd, SOL_SOCKET, SO_PEERTOKEN, &tokfd, &len);

kacs_impersonate_token(tokfd);
int filefd = openat(AT_FDCWD, requested_path, O_RDONLY);
/* if peer doesn't have access, openat fails with EACCES */
kacs_revert();
close(tokfd);
```

This pattern is the same as Windows' `ImpersonateNamedPipeClient` flow and is the right approach when the server is essentially a delegated-access proxy. The server doesn't make its own authorisation decision — it borrows the peer's identity and lets the kernel decide what's allowed.

## The connect-time vs send-time distinction

`SO_PEERCRED`, `SO_PEERSEC`, and `SO_PEERPIDFD` all snapshot at connect time and produce stable values for the connection's lifetime. `SO_PEERTOKEN` snapshots at the moment of the `getsockopt` call.

`SCM_CREDENTIALS` and `SCM_SECURITY` are per-message — the values reflect the sender's effective token at the moment of `sendmsg`. A peer that impersonates between messages produces `SCM_CREDENTIALS` reflecting the current impersonation; a peer that reverts produces values reflecting the primary identity again.

For most use cases, the connection-scoped primitives are sufficient. `SCM_CREDENTIALS` is needed for protocols where the same socket carries messages from different effective identities (rare).

## See also

- [Unix domain sockets](unix-domain-sockets) — the underlying socket types and address forms.
- [FD passing](fd-passing) — `SCM_RIGHTS` and the fd-bearer-authority model.
- [Primary vs impersonation tokens](../identity/primary-vs-impersonation-tokens) — what `SO_PEERTOKEN` returns and how to use it.
- [Credential projection](../linux-compatibility/credential-projection) — the projection mechanism behind `SO_PEERCRED`.
