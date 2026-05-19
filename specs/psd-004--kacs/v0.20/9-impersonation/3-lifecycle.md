---
title: Impersonation Lifecycle
---

## The sequence

1. **Client connects.** The client optionally sets the maximum impersonation level via syscall (default: Impersonation). The client calls `connect()`. The kernel's LSM hook fires on the Unix stream connection.

2. **Identity capture.** The hook examines the client thread's effective credential and the socket's max impersonation level:
   - **Anonymous:** a token whose user SID is `S-1-5-7`, whose enabled groups include Everyone, and which does not carry Authenticated Users is stored on the socket's LSM blob. The client's real identity is not recorded.
   - **Impersonation or Delegation:** the thread's effective token is stored. If the connecting thread is itself impersonating, the impersonated identity flows through — this is how identity cascades across local services.
   - **Identification:** the thread's effective token is stored but tagged at Identification level.

3. **Server impersonates.** The server calls `kacs_impersonate_peer` with the connection fd. The kernel retrieves the stored token and evaluates the two gates against the server thread's primary token. The effective level is computed. A new credential is constructed with the impersonation token at the resulting level.

4. **Access control.** All subsequent AccessCheck evaluations on this thread use the impersonation token. MIC uses the impersonation token's integrity level. PIP uses the PSB (unchanged).

5. **Revert.** The server calls `kacs_revert()`. The thread's credential is restored to `real_cred`. The thread is back to its service identity.

## Anonymous semantics

Any thread MAY impersonate the Anonymous identity without passing either gate. Assuming Anonymous is always a downgrade — the Anonymous token has no access rights beyond what is explicitly granted to `S-1-5-7` or Everyone. No privilege is needed, no identity gate check is performed, and no integrity ceiling applies.

Anonymous tokens carry the Anonymous SID (`S-1-5-7`) as the user SID, no
privileges, and Untrusted integrity. The socket path constructs this minimal
token shape instead of preserving any part of the caller's real identity.

## Double impersonation

If a thread is already impersonating and calls `kacs_impersonate_peer` again, the kernel internally reverts and then re-impersonates. The gates are evaluated against the primary token (unaffected by the previous impersonation).

## Interaction with MIC and PIP

**MIC uses the effective token** for tokens that are permitted to act because
the integrity ceiling in §9.2 makes acting impersonation safe. A thread MUST
NOT act at Impersonation or Delegation level with a client token whose integrity
level exceeds the server primary token's integrity level.

If the integrity ceiling fails, KACS caps the effective impersonation level to
Identification. The installed token MAY preserve the client's literal integrity
label as identity metadata, but that preserved label MUST NOT authorize resource
AccessCheck because Identification-level tokens are barred from AccessCheck by
§9.1. Therefore an acting impersonation token can only preserve or lower the
server primary token's integrity; a higher literal integrity label can exist
only on a non-acting Identification-level token.

**PIP uses the PSB** because there is no equivalent ceiling. PIP operates on `pip_type` and `pip_trust`, which are orthogonal to integrity level. If PIP read from the effective token, a process could impersonate a token carrying higher PIP values and gain protection it does not deserve.

## SeImpersonatePrivilege

SeImpersonatePrivilege permits a service to impersonate arbitrary clients — those with different user SIDs. Without it, a process can only impersonate tokens that match its own user SID and restriction status.

The privilege is checked against the server's **primary token**. A thread already impersonating one client has its privilege checked against its real service identity.

SeImpersonatePrivilege bypasses only the identity gate. It MUST NOT bypass the integrity ceiling. The privilege MUST be enabled at the time of the impersonation call.

## Delegation and the network boundary

Locally, Impersonation and Delegation are identical. The distinction activates at the network boundary: a Delegation-level token carries authorization for Kerberos credential forwarding to services on other machines.

KACS tracks the impersonation level on the token and the socket. When authd needs to perform Kerberos authentication on behalf of an impersonating thread, it checks the level. KACS has no Kerberos awareness and no network awareness — the level is a flag that authd interprets.

## Supported transports

Socket-based impersonation (`kacs_impersonate_peer`) is supported on two
socket types:

- **SOCK_STREAM** — connection-oriented byte stream.
- **SOCK_SEQPACKET** — connection-oriented with message boundaries. Uses the
  same identity capture model as stream.

Both use the same identity lifecycle: capture at `connect()`, impersonate via
`kacs_impersonate_peer`, revert via `kacs_revert`.

**Not supported for socket-based impersonation:**

- **SOCK_DGRAM** — connectionless. Identity would come via per-message
  credentials, which is a different model and not part of this syscall
  surface. In `v0.20`, datagram sockets do not create KACS peer tokens; a
  service that needs KACS identity on a datagram protocol must receive an
  explicit token fd and use `KACS_IOC_IMPERSONATE`.
- **socketpair-created sockets** — pre-connected and unnamed. Possession of
  the fd authorizes use of the channel, but `socketpair()` installs no KACS
  peer-token snapshot in `v0.20`.
- **Pipes / FIFOs** — no peer credential mechanism.

**Explicit token fd impersonation** (`KACS_IOC_IMPERSONATE`) works regardless
of how the token fd was obtained — socket-based, `SCM_RIGHTS` transfer,
`kacs_open_peer_token`, or any other path. This is the universal fallback for
transports that do not support socket-based impersonation.
