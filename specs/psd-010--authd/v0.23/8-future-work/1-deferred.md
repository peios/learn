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

## Elevation and linked tokens

UAC-style Full/Limited linked-token pairs and filtered tokens are
deferred. Token shaping (§5.2 step 5) is the hook; this version mints a
single primary token.

## Claims and Dynamic Access Control

Source-native claims already flow through the resolved principal (§4)
and onto the token; claim-transformation policy and the broader DAC
story are deferred.

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
