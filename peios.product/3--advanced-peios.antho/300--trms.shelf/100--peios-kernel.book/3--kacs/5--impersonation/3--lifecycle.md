---
title: Impersonation Lifecycle
description: Assuming and reverting an identity — the sequence, Anonymous, double impersonation, and how MIC and PIP interact with it.
---

## The sequence

**The client connects.** It optionally sets the maximum impersonation
level through a syscall — the default is Impersonation — and calls
`connect()`. The kernel's LSM hook fires on the Unix stream
connection.

**Identity is captured.** The hook examines the client thread's
effective credential together with the socket's maximum level. At
Anonymous, a token whose user SID is `S-1-5-7`, whose enabled groups
include Everyone, and which does not carry Authenticated Users is
stored on the socket's LSM blob, and the client's real identity is
never recorded. At Impersonation or Delegation, the thread's effective
token is stored — and if the connecting thread is itself
impersonating, the impersonated identity is what flows through, which
is how identity cascades across local services. At Identification, the
effective token is stored but tagged at that level.

**The server impersonates** by calling `kacs_impersonate_peer` with
the connection fd. The kernel retrieves the stored token, evaluates
both gates against the server thread's primary token, computes the
effective level, and constructs a new credential carrying the
impersonation token at that level.

**Access control follows the impersonation token.** Every subsequent
AccessCheck on the thread evaluates it, and MIC uses its integrity
level. PIP continues to read the PSB, unchanged.

**The server reverts** with `kacs_revert()`, restoring the thread's
credential to `real_cred` and its service identity with it.

## Anonymous

Any thread may impersonate the Anonymous identity without passing
either gate. Assuming Anonymous is always a downgrade — the token has
no access beyond what is explicitly granted to `S-1-5-7` or Everyone —
so no privilege is needed, no identity gate runs, and no integrity
ceiling applies.

Anonymous tokens carry the Anonymous SID as the user SID, no
privileges, and Untrusted integrity. The socket path constructs that
minimal shape rather than preserving any part of the caller's real
identity.

## Double impersonation

A thread already impersonating that calls `kacs_impersonate_peer`
again causes the kernel to revert internally and then re-impersonate.
Because the gates are evaluated against the primary token, the
previous impersonation has no bearing on the new one.

## Interaction with MIC and PIP

**MIC reads the effective token** for tokens permitted to act, which
is safe precisely because the integrity ceiling makes acting
impersonation safe. A thread cannot act at Impersonation or Delegation
level with a client token whose integrity exceeds the server primary
token's. When the ceiling caps the level to Identification, the
installed token may still preserve the client's literal label as
metadata, but it authorizes no resource access because
Identification-level tokens are barred from AccessCheck. An acting
impersonation token therefore preserves or lowers the server's
integrity, and a higher literal label can only ever exist on a
non-acting Identification-level token.

**PIP reads the PSB**, because there is no equivalent ceiling for it.
PIP operates on `pip_type` and `pip_trust`, which are orthogonal to
integrity level. Reading them from the effective token would let a
process impersonate a token carrying higher PIP values and acquire
protection it has not earned.

## SeImpersonatePrivilege

The privilege permits a service to impersonate arbitrary clients —
those with different user SIDs. Without it a process can impersonate
only tokens matching its own user SID and restriction status.

It is checked against the server's primary token, so a thread already
impersonating one client is judged on its real service identity. It
has to be enabled at the moment of the call. And it bypasses the
identity gate only, never the integrity ceiling.

## Delegation and the network boundary

Locally, Impersonation and Delegation behave identically. The
distinction activates at the network boundary, where a
Delegation-level token carries authorization for Kerberos credential
forwarding to services on other machines.

KACS tracks the level on the token and the socket, and authd checks it
when it needs to perform Kerberos authentication for an impersonating
thread. KACS itself has no Kerberos awareness and no network
awareness: the level is a flag that authd interprets.

## Supported transports

Socket-based impersonation through `kacs_impersonate_peer` works on
two socket types. `SOCK_STREAM` is the connection-oriented byte
stream, and `SOCK_SEQPACKET` is connection-oriented with message
boundaries and uses the same identity capture model. Both follow the
same lifecycle: capture at `connect()`, impersonate, revert.

Three transports do not support it. `SOCK_DGRAM` is connectionless, so
identity would arrive as per-message credentials — a different model
that is not part of this syscall surface; datagram sockets create no
KACS peer token. Sockets from `socketpair()` are pre-connected and
unnamed, and while possession of the fd authorizes use of the channel,
no peer-token snapshot is installed. Pipes and FIFOs have no peer
credential mechanism at all.

For all of these, the universal fallback is explicit token fd
impersonation through `KACS_IOC_IMPERSONATE`, which works regardless
of how the token fd was obtained — socket-based capture, an
`SCM_RIGHTS` transfer, `kacs_open_peer_token`, or any other path.
