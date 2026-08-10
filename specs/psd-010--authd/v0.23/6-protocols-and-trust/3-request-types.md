---
title: Request Types and Gates
---

This section defines the request taxonomy and the authorization gate for
each. Every gate is evaluated against the peer token (§6.2). Wire
framing is §6.3 below.

## authd client requests (`/run/authd.sock`)

| Request | Returns | Gate |
|---|---|---|
| **Logon** (credential-backed) | token fd + session id | **Knowledge of the credential.** Open to any peer that may connect; proving the credential *is* the authorization. Abuse is bounded by source lockout (§3.4), authd rate-limiting, and audit. |
| **LogonOnBehalf** (credential-less service logon) | token fd | Peer MUST hold **`SeTcbPrivilege`** (§6.2 — capability, not identity: authd checks the kernel-captured peer token, never "is this peinit"). This version mints a **Service (5)** logon for a base service identity (SYSTEM/LocalService/NetworkService) or a service-account (§5.4). Batch, credential-less Interactive/Network (secondary-logon), and domain S4U are deferred (§8); the gate is fixed now. |
| **ChangePassword** (forwarded, self-service) | status | **Knowledge of the old password** — which rides in the body and so survives the forward. authd routes by namespace and forwards it to the source's socket (§2.2, §7.2, §6.4 type 17). Serves the `must_change_password` flow (§5.1). Administrative reset (no old password) is **not** this request — it is the direct `SET_PASSWORD` on the admin socket, gated by the **Reset Password** control-access right on the target's SD (§7.2), because a forward cannot carry the caller's peer identity for the source to AccessCheck against. |
| **Query** (resolve self / permitted identity) | data | authd **impersonates the caller** (§6.2) and resolves under the caller's identity. |
| **Session management** (e.g. forced logout) | status | Peer MUST hold **`SeTcbPrivilege`**. |

The dividing line is: **credential-backed requests are gated by
knowledge and are open; credential-less requests are gated by
`SeTcbPrivilege`.** This mirrors the Windows boundary between
logon-with-credentials and acting as part of the TCB.

## Credential-backed Logon is open by design

Any peer that may connect to `/run/authd.sock` MAY attempt a Logon;
authd MUST NOT require a special privilege to *attempt* one. Knowledge
of the credential is the authorization, the resulting token's *use* is
still gated by the kernel, and online guessing is bounded by lockout
(§3.4), rate-limiting, and audit. An unprivileged caller that obtains a
token via Logon cannot necessarily *assign* it as a process's primary
token; the secondary-logon launch helper for that case is deferred
(§8).

## Throttling

Per-account lockout (§3.4) bounds hammering of a *single* account but not
**password-spray** (one guess each across many accounts), and the
mandatory argon2id per attempt — including the dummy for unknown
principals (§3.3) — makes an unthrottled credential attempt a CPU/memory
DoS on the source. authd MUST therefore throttle in addition to lockout:

- the throttle counts **every credential-verifying request** against the
  budgets — both `LOGON` and the forwarded self-service `CHANGE_PASSWORD`
  (whose old-password check is a verification against the same verifier,
  §3.3) — so an attacker cannot dodge the limit by switching verbs;
- a **per-caller (peer-SID)** attempt budget and a **global** attempt
  budget over a sliding window; once a budget is exceeded authd returns
  `RATE_LIMITED` (§6.4) **without** calling the source (so no argon2id is
  spent);
- both budgets are policy, with the defaults in §9.

Throttling is the bound on spray, the argon2id DoS, and lockout-induced
victim denial of service (§8.2).

## Source-transparent broker channel (`/run/authd/sources/*.sock`)

The source socket carries the operations authd forwards to a source:
verify-and-resolve (§4, §5.1), self-service ChangePassword (§7.2), and
credential-less Resolve for service-account logon (§5.4). All are gated by
the peer being **authd**. No other caller may use this interface.

## lpsd administration and setup (`/run/lpsd.sock`)

Administration requests are authorized by AccessCheck against the target
object's stored SD (§7.2). The setup-control request `ENTER_SETUP_MODE` is
different: it is accepted only before the store is initialised, is gated by
the peinit bootstrap authority (§7.1, §9), and is one-shot.

## Wire framing (overview)

Client and verify/resolve messages are **versioned, typed, binary**
(not JSON), consistent with the KACS wire formats and the PAC-isomorphic
contract (§4). Each message is a self-delimiting `SOCK_SEQPACKET`
datagram with an envelope `{ version, type, body }`; responses carry
`{ version, status, body }` and MAY carry a token fd via `SCM_RIGHTS`.
The exact byte layout of every message — the envelope, the type and
status enums, and each body including the resolved-principal record — is
defined normatively in §6.4.
