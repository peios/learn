---
title: Deferred Features
---

This chapter is informative. It records features that are part of the
subsystem's intended scope but are deliberately deferred to later
versions, so that the core (interactive local password logon and its
administration) can be specified and built first. Nothing here is
normative for this version; each item names the contracts already shaped
to accommodate it.

## CAAP distribution

authd is intended to read central access policies from the directory and
push them into the kernel policy cache before signalling readiness, and
to re-push on change. This is deferred. The policy phase (§5.2) runs on
a declared default policy until the rights-assignment/CAAP policy store
is wired.

## Domain join (adpsd, Active Directory, Kerberos)

The domain principal source (adpsd) fronting Active Directory via
Kerberos/NTLM is deferred. The seam (§2.2), the resolved-principal
contract (§4, PAC-isomorphic), the source registry (§6.1), and the
namespace-based routing (§2.2) are all shaped so that adpsd drops into
lpsd's structural position. adpsd is responsible for verifying a real
PAC's signatures and translating into the §4 contract, and for any
challenge–response on its remote hop (§6.2).

## Credential-less logon beyond Service

This version's `LOGON_ON_BEHALF` (§5.4) mints a **Service** logon only.
Deferred: **Batch** logon (scheduled tasks); credential-less
**Interactive/Network** logon (the `runas`/secondary-logon helper, also
listed below); protocol-transition **S4U** for a domain principal (part
of the domain-join work above — a service obtaining a token for a remote
domain user without their credential); and **managed** service-account
credentials (gMSA-style rotation), since a v1 purpose-made service account
(§5.4) is passwordless and machine-local. The `LOGON_ON_BEHALF` gate
(`SeTcbPrivilege`) and message shape are fixed now; these are additional
target/logon-type cases, not a format change.

## Elevation and linked tokens

UAC-style Full/Limited linked-token pairs and filtered tokens are
deferred. Token shaping (§5.2 step 5) is the hook; this version mints a
single primary token.

## Claims and Dynamic Access Control

Source-native claims already flow through the resolved principal (§4)
and onto the token; claim-transformation policy and the broader DAC
story are deferred.

## Protected-accounts guardrail

Principals and the domain object carry security descriptors and are
authorized by AccessCheck now (§7.2), so delegation is **expressible
today**: an administrator can grant any group Reset-Password or
create-child on the domain object, and it inherits to all principals.
Nothing about delegation itself is deferred, and no named preset (e.g. an
Account Operators default) is shipped or promised — a discouraged legacy
construct is not worth baking into the defaults when the SD model already
expresses delegation directly.

What **is** deferred is the guardrail that makes *broad* delegation safe.
Because the domain object is the single inheritance anchor (§7.2), a broad
delegation ACE inherits to every principal — including the built-in
Administrator, the `S-1-5-32` alias groups, and any regular user who is a
member of Administrators. Without protection, a delegated operator could
reset those principals' credentials and escalate. AD solves this with
AdminSDHolder/SDProp: members of protected groups get a locked-down SD
re-stamped over time. Peios defers the equivalent — a **membership-based
protected-SD** mechanism. Crucially, protection is keyed on **membership**
(is this principal an admin?), not on container placement: segregating the
built-ins into a separate container would shield only the *static*
built-ins and miss a regular user dynamically added to Administrators, so
container segregation is explicitly **not** the chosen tool. Until the
guardrail lands, deployments SHOULD keep the tight default (SYSTEM +
Administrators) and delegate narrowly.

OU-scoped (sub-container) delegation is a separate matter and is out of
scope entirely — not deferred — because lpsd is flat by design (§3):
hierarchical scoping is a directory-source concept (adpsd's AD backend),
not an lpsd feature (§7.2).

## Forced logout / revocation tooling

The userspace forced-logout pattern (walking `/proc/*/token` by
`auth_id` and signalling holders; PSD-004) is a session-management
request (§6.3) gated by `SeTcbPrivilege`. The tooling around it is
deferred.

**Security limitation (not merely deferred tooling).** KACS provides no
token-revocation primitive: tokens do not expire, a token fd passed via
`SCM_RIGHTS` to a process *outside* the session survives forced logout,
and account disable/delete takes effect only at the principal's next logon
(§7.2). "Log this user out now" is therefore best-effort, and the
`/proc/*/token` walk is racy — a holder may fork or pass its fd between
enumeration and signalling, so the walk MUST re-scan until no holder
remains. A real revocation guarantee depends on a future KACS
dead-logon-session facility, which this subsystem treats as a dependency.

## Additional credential factors

`webauthn`/passkey, `x509`/smartcard, and `recovery_code` factors reuse
the credential shape of §3.3 and are deferred.

## TPM-sealed at-rest protection

The `tpm-sealed` scheme and the optional argon2id pepper (§3.5) are
deferred until the platform's measured-boot story is solid enough to
seal against without brittle reseal-on-update failures. The wrappable
`secret_part` shape is mandated now so adoption is a re-wrap pass.

## Secondary-logon launch helper

A helper that lets an unprivileged caller launch a process on a token it
obtained via Logon (the `runas`/seclogon analogue) is deferred. Until
then, installing a returned token as a primary token requires the
appropriate privilege, which login frontends and peinit hold (§5.3).

## A Rust wrapper for `kacs_set_impersonation_level`

The client-side impersonation-level cap (§6.2) has no Rust binding yet.
Clients that need to cap the level below the default will require one.
