---
title: Impersonation Lifecycle
description: Assuming and reverting an identity — the sequence, Anonymous, double impersonation, and how MIC and PIP interact with it.
---

## The sequence

**The client connects.** It optionally sets the maximum impersonation
level on the socket with `setsockopt(SOL_KACS,
KACS_SO_IMPERSONATION_LEVEL)` — the default is Impersonation; the
option may be changed at any time and bounds every capture made from
then on — and calls `connect()`. The kernel's LSM hook fires on the
Unix stream connection.

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

**The server reads the peer token** with `getsockopt(SOL_KACS,
KACS_SO_PEER_TOKEN)` on the accepted connection, which opens a token fd
carrying `TOKEN_QUERY | TOKEN_IMPERSONATE` for the identity in that
end's conveyed-identity register — at this point, the identity captured
at connect (see *Per-message identity* below for how the register
moves).
**It impersonates** by installing that fd with `KACS_IOC_IMPERSONATE`:
the kernel evaluates both gates against the server thread's primary
token, computes the effective level, and constructs a new credential
carrying the impersonation token at that level. libpeios fuses the
two steps as `peios_token_impersonate_peer` for the handler that
impersonates, works and reverts on one thread.

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

A thread already impersonating that installs another token with
`KACS_IOC_IMPERSONATE` causes the kernel to revert internally and then
re-impersonate.
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

## Per-message identity

The connect-time capture is the first entry in a per-end
**conveyed-identity register**: the peer identity associated with the
data that end has consumed so far. Identity can also travel with the
data itself, as a `KACS_SCM_TOKEN` ancillary message under the
`SOL_KACS` level, and each such message the reader's position passes
advances the register. The anchor is the read position, never arrival:
a token still queued behind unread data is not yet visible, so a
handler can never be told an identity for a request it has not read.
`KACS_SO_PEER_TOKEN` returns a fresh fd to an immutable snapshot each
time; two calls may name different tokens, but a token never changes.

**Sending.** A sender conveys identity in one of two ways, and the
receiver cannot tell them apart, because both mean the same thing —
*the kernel verified that the sender could be this identity when it
sent these bytes*:

- Automatically, with `KACS_SO_PASS_TOKEN` set on the sending end:
  every send carries the sender's effective token, derived at the
  end's impersonation level. The derivation is cached against the
  effective token it was made from, so a run of sends under one
  identity costs one derivation. A thread that impersonates client A,
  writes to a pooled connection, reverts and writes again conveys A for
  the first write and its own identity for the second, with no change
  to the library doing the writing.
- Explicitly, by attaching a token fd in a `KACS_SCM_TOKEN` cmsg. The
  kernel gates the attach exactly as it would gate impersonating that
  token: the fd must carry `TOKEN_IMPERSONATE`, a primary token is
  first derived to an impersonation token at the end's level, and the
  two-gate model runs with the sender as installer. An attach the gates
  would cap below the token's own level fails with `EPERM` — an
  explicit act fails loudly where an install would silently downgrade.
  Attaching a token is therefore never more than impersonating it,
  sending, and reverting; it just avoids the install. A router
  forwarding on behalf of many clients re-attaches each client's token
  to the messages it forwards, and each downstream receiver gets a
  kernel-verified identity through the router.

Anonymous-level tokens attach without a gate, as assuming Anonymous is
always a downgrade. At most one token per message.

**Receiving.** Every skb a send produces carries the conveyed token, so
a large stream write conveys the same identity on all of its
fragments. A stream read stops at an identity boundary rather than
gluing bytes conveyed under different identities into one return,
which keeps the register exact even on a byte stream; on
`SOCK_SEQPACKET` one send is one message and one identity, which is
why it is the recommended type for Peios-native protocols. As the
reader's position passes conveyed data, the register moves to that
identity. `MSG_PEEK` neither advances the register nor consumes; a
`read()` or `splice()` that consumes data advances it just as
`recvmsg` does, because the register is kept at the point of
consumption, not where ancillary data is copied out.

A `KACS_SCM_TOKEN` cmsg — carrying a fresh `TOKEN_QUERY |
TOKEN_IMPERSONATE` fd — is delivered with a read when the receive call
supplied room for it and the read's identity differs from the register
the reader had before the read; otherwise nothing is delivered, and
`MSG_CTRUNC` is set only when a token was due and no room was
supplied. A handler that never reads ancillary data still has the
register: `recvmsg`, then `getsockopt(KACS_SO_PEER_TOKEN)`, gives the
identity of what it just read. Parsing the cmsg is the path for
pipelined or concurrent consumers that need the token bound to a
particular message.

`SOCK_DGRAM` sockets carry no register — many senders share one
receiving socket — so a datagram's token is delivered with every
datagram that carries one and is never retained.

## Supported transports

Peer-token capture works on two AF_UNIX socket types. `SOCK_STREAM`
is the connection-oriented byte stream, and `SOCK_SEQPACKET` is
connection-oriented with message boundaries and uses the same identity
capture model. Both follow the same lifecycle: capture at `connect()`,
read with `KACS_SO_PEER_TOKEN`, impersonate, revert — with per-message
identity layered on top as described above. `SOCK_DGRAM` supports
per-message identity only: `KACS_SO_PASS_TOKEN` and `KACS_SCM_TOKEN`
work, since a send needs no connection, and
`KACS_SO_IMPERSONATION_LEVEL` bounds them as on any socket, but there
is no register.

Where the register does not apply, `KACS_SO_PEER_TOKEN` reports which
case it is. On a datagram socket, or any non-Unix family, the option
fails with `EOPNOTSUPP`. A `socketpair()` end is connected but starts
with an empty register — no connect happened to capture anything — so
the option fails with `ENODATA` until the peer conveys an identity,
after which the register works as on any connection. A socket that is
not yet connected fails with `ENOTCONN`. Pipes and FIFOs are not
sockets at all, so `getsockopt` itself fails with `ENOTSOCK` before
KACS is reached.

For all of these, the universal fallback is explicit token fd
impersonation through `KACS_IOC_IMPERSONATE`, which works regardless
of how the token fd was obtained — the peer-token option, an
`SCM_RIGHTS` transfer, or any other path.
