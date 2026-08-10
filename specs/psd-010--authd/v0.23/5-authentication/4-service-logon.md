---
title: Service and Credential-less Logon
---

§5.1 covered the interactive password logon. A **service logon** mints a
token for a system service. It differs in two ways: there is no
credential (a TCB caller vouches instead), and the identity may be a
well-known service principal rather than a stored account. Everything
from the policy phase (§5.2) and the mint (§5.3) onward is identical to a
password logon.

## The caller vouches (no credential)

A service presents no password. peinit (or another TCB caller) requests
the token via **`LOGON_ON_BEHALF`** (§6.3, §6.4), gated on the peer token
holding `SeTcbPrivilege` (§6.2). The TCB caller's authority replaces
credential verification: authd mints what the vouching caller asks for,
within the constraints below. There is no source credential check and,
because a TCB-vouched request is not untrusted guessing, none of the
lockout, dummy-verifier, or throttle accounting of §3.3–§3.4 and §6.3
applies.

## This version: Service logon only

`LOGON_ON_BEHALF` this version supports **logon type Service (5)** only. A
request naming any other logon type is `INVALID_REQUEST`. Batch (scheduled
tasks), any credential-less Interactive/Network logon (the
secondary-logon/`runas` case), and protocol-transition **S4U** for a
domain principal are deferred (§8).

## Two target kinds, two resolve paths

The `target` of a service logon is one of two kinds, distinguished by
whether a stored account backs it:

1. **A base service identity** — a well-known service principal: SYSTEM
   (`S-1-5-18`), LocalService (`S-1-5-19`), or NetworkService
   (`S-1-5-20`). These are not stored in any source (§2.1); authd builds
   the resolved principal (§4) directly from the static catalogue and the
   idmap (§3.6). No source is contacted. The request MAY carry one or more
   **service-SID groups** (below).

2. **A purpose-made service account** — a stored lpsd principal created to
   run a service: an ordinary user record (`machine_sid`-relative RID)
   marked with the **service-account** account flag (§9) and holding **no
   credential**. (§3.3's ban on credential-free logon governs the
   *password* path; it does not constrain this TCB-vouched path.) authd
   resolves it through the source's **`RESOLVE`** request (§6.4) — the
   credential-less counterpart of verify/resolve: the source checks
   account state (disabled/expired) and returns the resolved principal
   (groups, primary group, POSIX projection), skipping only the credential
   verification. A disabled or expired service account is `DENIED`.

A `target` that is an ordinary **interactive user** account, a **domain**
principal, or a pseudo-principal is refused this version
(`INVALID_REQUEST`).

## Service SIDs are groups, not the identity

A per-service SID (`S-1-5-80-…`) is **not** a principal and is never a
`target`. It is a **group** the service carries for per-service access
control: the service runs *as* its base identity (usually
LocalService/NetworkService), and the service SID is added to the token's
group list so resources can be ACL'd to exactly that service. authd adds
each service-SID group the request names and — exactly as for any group
SID — merges the local groups that contain it via foreign-SID membership
(§3.2, §5.2 step 1): a service SID placed in a local group to grant the
service a right is resolved the same way a domain principal's local-group
membership is. The service SID is referenced as a member, never stored as
a principal (§3.1).

The isolation this yields is **SID-level, not uid-level**:
LocalService-hosted services share LocalService's user SID (and its
cosmetic POSIX uid — §3.6), while each carries a distinct service-SID
group. Because KACS decides access by SID and the uid carries no authority
(§3.6), the service-SID group is the real isolation boundary — which is
why a per-service *user* principal is unnecessary.

## Policy phase, the logon-rights gate, and mint

From the resolved principal onward the flow is standard: authd runs the
policy phase (§5.2) for logon type Service — privilege assignment over the
SID set (the base identity's row in §9 plus any groups), the Service
implicit groups (§9), integrity level — then mints the session and token
(§5.3), which peinit installs on the service it launches (§5.3).

The **logon-type rights gate** (§5.2 step 2) is, for this credential-less
path, satisfied by the vouching TCB caller's authority in lieu of a
per-principal Service right: peinit configuring a service to run *is* the
administrative decision the Service logon-right encodes, and the
per-service rights-assignment store that would record it is deferred with
CAAP (§8). When that store lands, the per-principal Service gate applies
to service logons as it does to credentialed ones.
