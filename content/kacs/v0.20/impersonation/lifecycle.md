---
title: Impersonation Lifecycle
order: 3
---

## The sequence

1. **Client connects.** The client optionally sets the maximum impersonation level via syscall (default: Impersonation). The client calls `connect()`. The kernel's LSM hook fires on the Unix stream connection.

2. **Identity capture.** The hook examines the client thread's effective credential and the socket's max impersonation level:
   - **Anonymous:** a token containing only `S-1-5-7` is stored on the socket's LSM blob. The client's real identity is not recorded.
   - **Impersonation or Delegation:** the thread's effective token is stored. If the connecting thread is itself impersonating, the impersonated identity flows through — this is how identity cascades across local services.
   - **Identification:** the thread's effective token is stored but tagged at Identification level.

3. **Server impersonates.** The server calls `kacs_impersonate_peer` with the connection fd. The kernel retrieves the stored token and evaluates the two gates against the server thread's primary token. The effective level is computed. A new credential is constructed with the impersonation token at the resulting level.

4. **Access control.** All subsequent AccessCheck evaluations on this thread use the impersonation token. MIC uses the impersonation token's integrity level. PIP uses the PSB (unchanged).

5. **Revert.** The server calls `kacs_revert()`. The thread's credential is restored to `real_cred`. The thread is back to its service identity.

## Anonymous semantics

Any thread MAY impersonate the Anonymous identity without passing either gate. Assuming Anonymous is always a downgrade — the Anonymous token has no access rights beyond what is explicitly granted to `S-1-5-7` or Everyone. No privilege is needed, no identity gate check is performed, and no integrity ceiling applies.

## Double impersonation

If a thread is already impersonating and calls `kacs_impersonate_peer` again, the kernel internally reverts and then re-impersonates. The gates are evaluated against the primary token (unaffected by the previous impersonation).

## Interaction with MIC and PIP

**MIC uses the effective token** because the integrity ceiling makes it safe. A thread can never hold an impersonation token with a higher integrity level than its primary token. MIC can trust the effective token because impersonation can only lower integrity, never raise it.

**PIP uses the PSB** because there is no equivalent ceiling. PIP operates on `pip_type` and `pip_trust`, which are orthogonal to integrity level. If PIP read from the effective token, a process could impersonate a token carrying higher PIP values and gain protection it does not deserve.

## SeImpersonatePrivilege

SeImpersonatePrivilege permits a service to impersonate arbitrary clients — those with different user SIDs. Without it, a process can only impersonate tokens that match its own user SID and restriction status.

The privilege is checked against the server's **primary token**. A thread already impersonating one client has its privilege checked against its real service identity.

SeImpersonatePrivilege bypasses only the identity gate. It MUST NOT bypass the integrity ceiling. The privilege MUST be enabled at the time of the impersonation call.

## Delegation and the network boundary

Locally, Impersonation and Delegation are identical. The distinction activates at the network boundary: a Delegation-level token carries authorization for Kerberos credential forwarding to services on other machines.

KACS tracks the impersonation level on the token and the socket. When authd needs to perform Kerberos authentication on behalf of an impersonating thread, it checks the level. KACS has no Kerberos awareness and no network awareness — the level is a flag that authd interprets.
