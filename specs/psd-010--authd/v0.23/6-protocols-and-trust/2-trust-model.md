---
title: Caller Trust Model
---

The trust model answers "who may ask the subsystem for what." It rests
on the kernel peer-token primitives of PSD-004, which let a server learn
the *token* of the process that connected to it, race-free.

## Identifying the caller

On each connection, a server (authd, or a source/admin interface) MUST
obtain the caller's identity with **`kacs_open_peer_token`** (PSD-004),
which returns a token fd for the peer-identity snapshot captured at
`connect()`. The returned token carries `TOKEN_QUERY | TOKEN_IMPERSONATE`.
A server MUST treat `-EACCES` (no captured peer token — e.g. a
datagram/`socketpair` socket) as a hard reject, and MUST NOT fall back to
`SO_PEERCRED`/`SCM_CREDENTIALS`, which are forgeable.

A server MUST authorize each request against this **peer token**, never
against identity claims carried in the request body.

The snapshot is captured at `connect()`, so it is immune to PID reuse.
This immunity is load-bearing; PSD-004 §13.1 implies but does not yet
*normatively guarantee* it, so PSD-010 takes it as an explicit
**dependency** on KACS (to be asserted normatively there). A TCB client
MUST NOT pass a live authd connection across a privilege boundary — doing
so would make authd treat the channel as that TCB client (an fd-handoff
confused deputy).

## The governing principle

authd holds TCB power and MUST use the minimum of it:

- **authd uses its own (TCB) authority only to mint** sessions and
  tokens.
- **For work that must be bounded by the caller's rights** (e.g. an
  identity query that should reveal only what the caller may see), authd
  MUST impersonate the caller with **`kacs_impersonate_peer`** (PSD-004),
  perform the work under the caller's identity, and then revert with
  **`kacs_revert`**. This prevents authd from acting as a confused
  deputy. All caller-bounded work MUST occur strictly between the
  impersonate and the revert, and authd MUST check the
  `kacs_impersonate_peer` result: if the kernel silently capped the level
  below IMPERSONATION, authd MUST fail the request rather than fall back to
  acting under its own TCB authority.

## Client-set impersonation level

A client MAY cap how far a server may impersonate it by calling
`kacs_set_impersonation_level` before `connect()` (PSD-004; default
IMPERSONATION). Servers MUST honour the cap the kernel enforces. (No
Rust wrapper for this syscall exists yet; clients that need to cap the
level will require one — see §8.)

## Local IPC is trusted

The source/broker hop and the admin hop are local IPC between
kernel-authenticated endpoints; there is no network adversary on these
paths. Accordingly the resolved principal carries no signature (§4) and
the credential crosses in the clear (§6.2.5 below). This trust assumption
is specific to the local sockets and does not extend to any future
network hop, which a source handles internally (§8).

## Credential handling

For an interactive logon the cleartext password necessarily reaches
authd (the client holds it and must get it to the verifier). authd MUST
forward it unmodified to the source (credential pass-through — the
source owns all hashing/derivation), MUST hold it in `mlock`'d memory,
MUST zeroize it immediately after forwarding, and MUST NOT log or
persist it. A challenge–response scheme, where used at all, belongs only
to a source's *remote* hop (e.g. a domain source to its KDC), never to
the local broker/source hop.
