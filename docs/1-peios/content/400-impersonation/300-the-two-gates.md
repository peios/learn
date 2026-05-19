---
title: The two-gate model
type: concept
description: When a server impersonates a client, the kernel decides what level the server actually ends up with by running two independent gates. The identity gate asks "is the server allowed to impersonate this user?". The integrity ceiling asks "may the impersonation token's integrity exceed the server's own?". This page covers both gates and the silent downgrade behaviour they produce.
related:
  - peios/impersonation/overview
  - peios/impersonation/impersonation-levels
  - peios/impersonation/peer-tokens
---

When a server impersonates a client, it does not automatically get the level the client granted on the socket. The kernel runs two independent gates first. Each gate can lower the effective level. The granted level is the minimum the two gates permit.

The two gates are:

1. The **identity gate** — is the server allowed to impersonate this particular user's identity?
2. The **integrity ceiling** — may the impersonation token's integrity level exceed the server's own?

Each gate is checked independently. Failing either one is silent: the impersonation call still succeeds, the level is silently capped, and the server only finds out by inspecting the resulting token. The kernel deliberately does not raise an error, because the requested level is the *maximum* — any lower level is a valid outcome.

There is one case where the kernel refuses outright with `-EPERM` rather than downgrading. That case is covered below.

## Gate 1: identity

The identity gate asks: **does the server have authority to impersonate this specific user?** It has two ways to pass:

- The server's primary token has the **same user SID** as the client. A process can always impersonate its own user, regardless of privileges.
- The server's primary token holds **`SeImpersonatePrivilege`**. The privilege explicitly grants the right to assume any user's identity.

If neither is true, the identity gate fails. The token still gets installed, but the effective level is capped at **Identification** — the server can inspect the client's identity but cannot use the token for any access check.

The split is deliberate. A service whose job is handling user requests — a file share, a database, the registry daemon — holds `SeImpersonatePrivilege` and can impersonate any user. A process running as user X can act as user X without any special privilege. Code that holds neither — a random user-mode process trying to install some other user's token — is restricted to inspection only.

`SeImpersonatePrivilege` is one of the few privileges that authd grants liberally to services in the role-policy assignment. Almost every service that handles user requests has it. The privilege is what distinguishes "code authorised to act as users" from "code that happened to receive a token fd".

## Gate 2: integrity ceiling

The integrity ceiling asks: **does the impersonation token's integrity level exceed the server's own primary token's integrity level?**

If it does — the client has High integrity, the server has Medium — the impersonation token's integrity is silently capped at the server's level. The token still installs, the level granted by the identity gate is preserved, but the token's integrity is now Medium instead of High. Every subsequent access check uses the capped integrity.

The motivation is concrete. Without the ceiling, a Medium-integrity service that captured a High-integrity client's token would suddenly be operating at High integrity for the duration of the request. That breaks the integrity model — a process's effective ceiling should be bounded by what it would have had on its own.

The ceiling is **always** enforced. `SeImpersonatePrivilege` does **not** bypass it. There is no privilege that does. A service that needs to operate at High integrity on behalf of a High-integrity client must itself run at High integrity.

## Composition: the minimum permitted

The two gates are independent. Each one decides what level it permits:

| Identity gate result | Integrity ceiling result | Granted level |
|---|---|---|
| Pass at full level | Token's integrity is at or below server's | **The level the client granted on the socket.** |
| Pass at full level | Token's integrity exceeds server's | The level the client granted, **but integrity is capped at server's level**. |
| Fail (no same-SID, no SeImpersonate) | Token's integrity is at or below server's | **Identification.** Token installs, server can inspect, but no AccessCheck will pass. |
| Fail | Token's integrity exceeds server's | **Identification, with integrity capped.** Same as the above, plus the integrity downgrade. |

The granted level is the minimum the two gates permit. Neither gate fails the operation; both can downgrade it. The downgrade is silent.

## The silent downgrade

This is the consequence worth memorising: **impersonation never errors on policy failure. It silently downgrades.**

A server that calls `kacs_impersonate_peer(fd)` and gets a successful return does not know whether the resulting token has the level it expected. Both an Impersonation-level token and an Identification-level token can come out of the same call, with no error in either case. The only way to tell is to query the token after install.

Code that wants to detect a downgrade has to do something like:

1. Call `kacs_impersonate_peer(fd)` (or the explicit-fd variant).
2. Open the thread's effective token.
3. Read `impersonation_level` via `KACS_IOC_QUERY`.
4. Branch on the result: proceed if Impersonation or Delegation, log-and-skip if Identification or Anonymous.

The reason for the silent design is that the gates are bounded by policy and the policy is the operator's decision. A service may legitimately want to handle requests from clients regardless of whether it can fully impersonate them — recording who asked for what even when it cannot act as them is useful. Making the downgrade an error would force every server to either bypass the failure or refuse to handle the request, neither of which is the right default.

## The one hard-deny case

There is exactly one situation where impersonation fails with an error rather than downgrading: **a restricted token attempting to impersonate an unrestricted token of the same user**.

The kernel refuses with `-EPERM`. The impersonation does not happen, the thread does not get a new token, the call returns an error.

The reason is sandbox-escape prevention. A process running on a restricted token — a sandbox process, an anti-malware quarantine — is supposed to have narrowed identity. If that process could impersonate an unrestricted version of the same user, the restriction would be trivially escapable: capture any token fd belonging to the same user (which the sandbox could obtain via socket peer capture or other means), impersonate, and suddenly the sandbox is running with full user identity.

The hard-deny applies specifically to the **same-user** case. A restricted process can still impersonate a different user's token, subject to the normal gates. It just cannot use impersonation as a way to "promote" itself back to the unrestricted version of its own identity.

This is the only impersonation case that errors. Every other policy failure is silent.

## Double impersonation

A thread that is already impersonating can install a second impersonation token. The kernel handles this by silently reverting the first impersonation before installing the second — there is no nesting.

The gates are evaluated against the **primary token**, not the current impersonation. Whatever the thread was previously impersonating does not affect what it can impersonate next. The primary's identity and privileges (notably `SeImpersonatePrivilege`) are what the kernel reads to decide both gates.

## When the gates do *not* apply

The gates fire on impersonation install. They do not fire on:

- **Reverting.** `kacs_revert` always succeeds and does not consult the gates.
- **Reading a token.** `kacs_open_peer_token` or `kacs_open_thread_token` returns a token fd without impersonating; the gates only run when the token is actually installed on a thread.
- **Process token operations.** Opening another process's primary token (`kacs_open_process_token`) is governed by the process SD and PIP dominance, not the impersonation gates.

The gates are specifically about *installing* a foreign identity on a thread. Reading information about a token is a different operation governed by different checks.

## The principle behind the model

The two-gate model is the kernel's enforcement of one rule: **a thread can never end up at a higher effective trust level than it could have reached on its own**.

The identity gate makes sure the impersonation has authority behind it: either the same user, or the explicit `SeImpersonatePrivilege` that says "this service handles users by design". The integrity ceiling makes sure the impersonation cannot raise the server's effective integrity. Together they bound impersonation to what the server's own primary token would have permitted.

Everything else is a consequence. The silent downgrade exists because the requested level is a maximum, not a promise. The restricted-token hard-deny exists because that one case is the only way a same-user impersonation could increase authority rather than decrease it. The PIP exclusion (covered in [Process integrity protection](~peios/process-integrity-protection/overview)) is the same rule applied to the binary's trust label: PIP is a property of the binary, not of an identity, and impersonation does not change which binary is running.
