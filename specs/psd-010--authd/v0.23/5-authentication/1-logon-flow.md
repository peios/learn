---
title: The Logon Flow
---

A logon turns a presented credential into a token. This section defines
the end-to-end flow for an interactive local password logon — the core
case. The policy phase is detailed in §5.2 and the mint in §5.3.

## Sequence

1. A client (e.g. a login frontend) collects the principal name and
   password and sends a **Logon** request to authd (§6.3), naming the
   logon type (Interactive).
2. authd captures the caller's peer token (§6.2) for authorization and
   audit, and routes by the principal's namespace (§2.2) to a source.
3. authd forwards the principal name and the transient credential,
   unmodified, to the source's verify/resolve interface (§6.1). authd
   does not hash, salt, or otherwise transform the credential
   (credential pass-through — §6.2.5).
4. The source verifies and resolves (below) and returns a resolved
   principal (§4) with a tri-valued `status`.
5. On `status = ok`, authd runs the policy phase (§5.2), then mints the
   session and token (§5.3), and returns the token to the client (§6.3).
6. authd emits a logon audit event (§5.1 below) for every outcome.

## What the source does (verify and resolve)

On a verify/resolve request the source MUST, in order:

1. **Look up** the named principal. If absent, perform the dummy
   verification of §3.3 and return the uniform `denied` of step 4 below.
2. **Check account state** — disabled, locked (`lockout_until`),
   expired (`account_expires`). If any fails, return `denied(reason)`.
3. **Verify the credential** (argon2id, constant-time — §3.3).
4. **Update logon-path state** (a write): on failure, increment
   `bad_pw_count`, stamp `last_bad_pw_time`, and set `lockout_until` if
   the threshold is reached; on success, reset `bad_pw_count`, clear
   `lockout_until`, stamp last-logon, and optionally re-wrap the verifier
   (§3.4).
5. **Resolve identity** — expand groups within the namespace
   (cycle-guarded — §3.2), gather claims, flags, primary group, and the
   POSIX projection, and build the resolved principal (§4).

## Check precedence and atomicity

When more than one condition applies, the source MUST resolve them in
this precedence (first match wins): **account locked** > **account
disabled or account-expired** > **wrong credential** > **password
expired (`must_change_password`)**. Thus a wrong credential on an
otherwise-valid account is `denied`, while a *correct* credential on an
account whose password has exceeded its maximum age — and which is not
locked, disabled, or account-expired — is `must_change_password`. A
correct credential MUST reset lockout state (step 4) even when the result
is `must_change_password`.

All `denied` paths — including those decided by account state before the
credential is checked — MUST be timing-equalized per §3.3: where the real verification was
skipped, the source computes the argon2id dummy over the presented
credential and then zeroizes it, so that neither account existence nor
account state is observable via timing.

The logon-path state update (step 4) MUST be a single atomic transaction
(§3.5) committed **before** the source returns, so that concurrent failed
verifications cannot lose increments and a returned `denied` reflects
committed lockout state.

## Tri-valued status

The source's `status` MUST be one of:

- **`ok`** — verified; the resolved principal is complete.
- **`denied(reason)`** — not verified, or account state forbids logon.
  The `reason` is for audit and frontends; the failure presented to the
  caller MUST NOT distinguish "no such principal" from "wrong password"
  (§3.3).
- **`must_change_password`** — the credential is *valid* but the
  password is expired and must be changed. The broker MUST NOT mint a
  token for this status. The client must complete a ChangePassword
  (§7.2) — which the broker forwards source-transparently (§2.2) — and
  then retry the logon.

## Timing and enumeration

The source MUST equalise the timing of the `denied` paths so that
account existence is not observable (§3.3). The broker MUST NOT add a
side channel (e.g. a different error for unknown principal) of its own.

## Audit

authd MUST emit a KMES audit event for every logon attempt, carrying at
least: the target principal, the logon type, the source, the captured
caller identity, the outcome, and (on success) the session id. The
event MUST NOT contain the cleartext credential.
