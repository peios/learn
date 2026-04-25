---
title: Impersonation Lifecycle
---

## The sequence

1. **Client connects.** The client optionally sets the maximum impersonation level via syscall (default: Impersonation). The client calls `connect()` on a Unix stream (SOCK_STREAM) or seqpacket (SOCK_SEQPACKET) socket. The kernel's LSM hook (`security_unix_stream_connect`, which fires for both stream and seqpacket) captures the client's identity.

2. **Identity capture.** The hook examines the client thread's effective credential and the socket's max impersonation level:
   - **Anonymous:** a token containing only `S-1-5-7` is stored on the socket's LSM blob. The client's real identity is not recorded.
   - **Impersonation or Delegation:** the thread's effective token is stored. If the connecting thread is itself impersonating, the impersonated identity flows through — this is how identity cascades across local services.
   - **Identification:** the thread's effective token is stored but tagged at Identification level.

3. **Server impersonates.** The server calls `kacs_impersonate_peer` with the connection fd. The kernel retrieves the stored token and evaluates the two gates against the server thread's primary token. The effective level is computed. A new credential is constructed with the impersonation token at the resulting level. The credential holds its own reference to the token (refcount incremented). Closing the source socket or token fd after this point does not revoke impersonation — the credential's reference keeps the token alive.

4. **Access control.** All subsequent AccessCheck evaluations on this thread use the impersonation token. MIC uses the impersonation token's integrity level. PIP uses the PSB (unchanged).

5. **Revert.** The server calls `kacs_revert()`. The thread's credential is restored to `real_cred`. The impersonation credential is freed, dropping its token reference. The thread is back to its service identity.

## Anonymous semantics

Any thread MAY impersonate the Anonymous identity without passing either gate. Assuming Anonymous is always a downgrade — the Anonymous token has no access rights beyond what is explicitly granted to `S-1-5-7` or Everyone. No privilege is needed, no identity gate check is performed, and no integrity ceiling applies.

Anonymous tokens carry only the Anonymous SID (`S-1-5-7`) as the user SID, no privileges, and Untrusted integrity. This applies uniformly regardless of how the Anonymous token was obtained:

- **Socket path:** `kacs_impersonate_peer` at Anonymous level constructs a minimal token from scratch. The client's real identity is not recorded.
- **Duplicate path:** `KACS_IOC_DUPLICATE` with target impersonation_level=Anonymous strips the source token's identity. The duplicate is a minimal Anonymous token, not a copy of the source with the level flag changed. The source token's user SID, groups, privileges, and claims are not carried forward.

This ensures Anonymous is an identity boundary, not a cosmetic flag. A service that needs to "drop identity" for an operation can duplicate its client token to Anonymous and impersonate the result.

### Anonymous-in-Everyone policy

A system-wide kernel setting controls whether Anonymous tokens include Everyone (`S-1-1-0`) in their group list:

- **Default (secure): excluded.** Anonymous tokens have no group memberships. They can only match ACEs targeting `S-1-5-7` explicitly. ACEs targeting Everyone do NOT match. This is the recommended setting and the default at boot.
- **Permissive: included.** Anonymous tokens include Everyone as a group. ACEs targeting Everyone match Anonymous tokens. This is less secure — a targeted deny on a specific user SID can be bypassed by going Anonymous, since the deny no longer matches but the Everyone allow does.

The setting is stored in the registry and read by the kernel at boot. It can be changed at runtime via a privileged syscall (SeTcbPrivilege required). The setting applies to all Anonymous token construction — both the socket path and the duplicate path.

> [!INFORMATIVE]
> Windows has the same setting: `HKLM\SYSTEM\CurrentControlSet\Control\Lsa\EveryoneIncludesAnonymous`. The default on modern Windows is 0 (excluded). Peios follows the same secure default.

## Double impersonation

If a thread is already impersonating and calls `kacs_impersonate_peer` again, the kernel internally reverts and then re-impersonates. The gates are evaluated against the primary token (unaffected by the previous impersonation).

## Interaction with MIC and PIP

**MIC uses the effective token** because the integrity ceiling makes it safe. A thread can never hold an impersonation token with a higher integrity level than its primary token. MIC can trust the effective token because impersonation can only lower integrity, never raise it.

**PIP uses the PSB** because there is no equivalent ceiling. PIP operates on `pip_type` and `pip_trust`, which are orthogonal to integrity level. If PIP read from the effective token, a process could impersonate a token carrying higher PIP values and gain protection it does not deserve.

## SeImpersonatePrivilege

SeImpersonatePrivilege permits a service to impersonate arbitrary clients — those with different user SIDs. Without it, a process can only impersonate tokens that match its own user SID and restriction status.

The privilege is checked against the server's **primary token**. A thread already impersonating one client has its privilege checked against its real service identity.

SeImpersonatePrivilege bypasses only the identity gate. It MUST NOT bypass the integrity ceiling. The privilege MUST be enabled at the time of the impersonation call.

## Supported transports

Socket-based impersonation (`kacs_impersonate_peer`) is supported on two socket types:

- **SOCK_STREAM** — connection-oriented byte stream. The standard IPC transport for Peios services.
- **SOCK_SEQPACKET** — connection-oriented with message boundaries. Same identity capture model as stream (same LSM hook, same `SO_PEERCRED`). Useful for services that need message framing.

Both use the same identity lifecycle: capture at `connect()`, impersonate via `kacs_impersonate_peer`, revert via `kacs_revert`.

**Not supported for socket-based impersonation:**

- **SOCK_DGRAM** — connectionless. Identity would come via per-message `SCM_CREDENTIALS`, which is a fundamentally different model (no persistent peer, per-message identity). Under KACS, `CAP_SETUID` is ALLOW, so any process can forge `SCM_CREDENTIALS` — the identity assertion is not trustworthy. Services using datagram sockets that need client identity SHOULD use explicit token fd passing (`SCM_RIGHTS` + `KACS_IOC_IMPERSONATE`) instead.
- **Pipes / FIFOs** — no peer credential mechanism.

**Explicit token fd impersonation** (`KACS_IOC_IMPERSONATE`) works regardless of how the token fd was obtained — socket-based, `SCM_RIGHTS` transfer, `kacs_open_peer_token`, or any other path. This is the universal fallback for transports that don't support socket-based impersonation.

## Per-call level constraint

KACS_IOC_IMPERSONATE uses the token's own `impersonation_level` (subject to gate capping). There is no per-call max-level parameter equivalent to Windows's `SECURITY_QUALITY_OF_SERVICE`.

If a service holds a Delegation-level token but needs only Impersonation-level access, it SHOULD duplicate the token to Impersonation level first via KACS_IOC_DUPLICATE, then impersonate the duplicate. This is the standard pattern for defense-in-depth: hold the minimum impersonation level needed for the operation.

## Thread-to-thread impersonation

KACS does not support direct thread-to-thread impersonation (Windows's `NtImpersonateThread`). Impersonation is established via socket peer identity (`kacs_impersonate_peer`) or explicit token fd (`KACS_IOC_IMPERSONATE`). There is no mechanism for thread A to directly assume thread B's client identity without an intermediate token fd.

This is an architectural simplification. In Windows, thread-to-thread impersonation is used for RPC dispatch where a receiving thread needs to assume a client thread's identity. In KACS, the equivalent workflow uses socket-based impersonation or explicit token passing via fd.

## Delegation and the network boundary

Locally, Impersonation and Delegation are identical. The distinction activates at the network boundary: a Delegation-level token carries authorization for Kerberos credential forwarding to services on other machines.

KACS tracks the impersonation level on the token and the socket. When authd needs to perform Kerberos authentication on behalf of an impersonating thread, it checks the level. KACS has no Kerberos awareness and no network awareness — the level is a flag that authd interprets.
