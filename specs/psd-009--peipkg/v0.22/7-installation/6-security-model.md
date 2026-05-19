---
title: Security Model
---

This section describes the privilege model the package
manager operates under and the audit obligations it
carries. Both are Peios-specific concerns that build on
KACS (PSD-004) and KMES (PSD-008).

## Privilege model

The package manager holds no principal, identity, or
access rights of its own. It runs **as the calling
operator**: every file operation it performs — creating,
replacing, or deleting a payload file — is checked by
KACS (PSD-004) against the *caller's* token and the
target's security descriptor. If the caller is authorised
the operation succeeds; if not, it fails. The package
manager contributes no authority.

The authority to install a package is therefore exactly
the authority to write the directories the package
installs into — an ordinary matter of security
descriptors on `/usr/`, `/etc/`, `/var/`, and `/opt/`. A
deployment grants installation authority by granting
those write rights to whichever principals it intends to
be able to install software (typically a system
administrators group).

A consequence: a package's manifest-declared SD overrides
(§3.4.7) can only assign security descriptors the calling
operator already has the authority to assign. A package
cannot, through the package manager, obtain authority the
operator running it does not hold. Where §3.4.7 and
PSD-004 require a particular right to apply a given SD —
for example `WRITE_DAC` for a DACL, or `WRITE_OWNER` and
`SeRestorePrivilege` for an owner-SID assignment — that
right MUST be held by the *operator*, not by the package
manager.

> [!INFORMATIVE]
> Earlier drafts ran the package manager as a dedicated
> KACS service principal holding broad system rights — a
> posture comparable to a Linux root process. Peios
> instead makes the package manager an ordinary,
> unprivileged program: there is no standing principal to
> compromise, no privilege to confine, and the blast
> radius of running a malicious package is bounded by the
> authority of whoever ran it. Scoped, curated
> installation — letting a low-authority operator install
> a specific approved package without granting general
> write access — is *not* provided by the package
> manager; it is the responsibility of the higher-level
> roles and features layer (§1), which can act as a
> privileged broker.

## Blast radius

Because the package manager holds no principal of its own
(§7.6, "Privilege model"), there is no standing
privileged identity to confine and no privileged process
to compromise. The authority exercised during an install
is the calling operator's, and only for the duration of
that invocation.

The blast radius of installing a malicious or defective
package is therefore bounded, precisely, by the authority
of the operator who installed it: a malicious package can
do nothing the operator could not already do directly.
This makes the trust decision — which repositories an
operator configures, and which packages an operator with
broad authority chooses to install — the operative
security boundary. Signature verification (chapter 5) and
the repository trust model (§6.5) exist to inform that
decision; they do not substitute for it.

The package manager does not require, and SHOULD NOT be
run with, authority beyond what installation needs: write
access to the payload destinations of §3.4.1, and network
access to fetch from configured repositories. It performs
no `kexec`, loads no kernel modules except via the
`depmod` side effect (§4.3), loads no BPF programs, and
writes no registry state — its own bookkeeping is a
private store (§7.4.5.1), not the registry.

## Audit

Every install, upgrade, uninstall, refresh, and recovery
operation MUST emit an audit event. The package manager
emits events through the `kmes_emit` system call into
KMES, the kernel event subsystem (PSD-008). Because
emission is a local kernel call and not a message to a
userspace daemon, it has no "destination unreachable"
failure mode: there is no reachability probe, no
fail-closed-on-unavailable rule, and no audit-retention
journal. Whether and when KMES events are drained and
persisted is the concern of eventd, not of the package
manager.

An emitted event MUST include at minimum:

- Operation type (install, upgrade, uninstall, refresh,
  recovery)
- The calling operator's KACS identity
- Target package(s): name, version, architecture
- Source repository (for install and upgrade)
- Outcome (success, rejection, rollback), with a
  rejection reason where applicable
- Transaction identifier
- An RFC 3339 UTC timestamp

The package manager MUST emit a success event for a
committed operation and a separate failure event for one
that is rejected or rolled back.

> [!INFORMATIVE]
> The package manager's own audit events are a
> semantically meaningful summary of an operation. They
> are not the security boundary: the authoritative record
> of what changed on disk is the kernel's own audit of
> the underlying file operations (KACS → KMES), which the
> calling operator cannot suppress. A forged or omitted
> peipkg event cannot conceal a file operation from the
> kernel's record.

### Canonical event types

Audit events emitted by the package manager MUST use
event-type strings drawn from the following set so that
KMES per-event-type access control (PSD-008) can target
peipkg events precisely:

| Event type | Emitted for |
|---|---|
| `peipkg.install` | A successful install operation |
| `peipkg.upgrade` | A successful upgrade operation |
| `peipkg.uninstall` | A successful uninstall operation |
| `peipkg.refresh` | A successful repository refresh |
| `peipkg.transaction-failed` | A transaction that was rolled back |
| `peipkg.recovery` | A recovery-mode resolution |
| `peipkg.authorisation` | An operator authorisation evidence record |
| `peipkg.repo-add` | A repository add operation |
| `peipkg.repo-remove` | A repository remove operation |
| `peipkg.config-change` | A trust-policy or transport-flag change |

The `origin_class` for all peipkg events is `peipkg`.
Future versions of this specification MAY add additional
event-type strings to this set; consumers of the audit
stream MUST treat unknown event types as informational
(not as errors).

## Trust anchor distribution

Trust anchors for the official Peios repository (the
fingerprints used at repo-add per §6.5.2) MUST be
available to the package manager from the OS image — a
file installed by the base system, outside any package.
The exact path is operationally defined; a future PSD
covering OS-image construction is expected to standardise
it.

Custom-repository trust anchors are supplied by the
operator at repo-add time per §6.5.2.

> [!INFORMATIVE]
> Bootstrap trust is a property of the OS image and the
> initial-boot procedure, not of the package format: the
> package manager relies on the official anchors being
> present when it first runs.
>
> The intended end state distributes those anchors
> redundantly — additionally as a registry key (PSD-005)
> populated at first boot — and has the package manager
> cross-check every available source byte-for-byte,
> refusing repository operations on disagreement (with
> the OS-image source authoritative) and on a missing
> source in a rescue-media boot context. That redundancy
> defends against corruption or silent substitution of a
> single source. It depends on the registry (LCS) being
> available; until then the OS-image file is the single
> source and the cross-source check is inert. The model
> is additive: once the registry source exists, the
> cross-check applies without changing the OS-image
> source's role as authoritative.

## Clock dependence

Several normative checks depend on the local system
clock: signing-key `valid_until` timestamps (§6.1.4),
maximum trusted age (§6.5.4), maximum index staleness
(§6.2), and build provenance timestamps (§3.3.4). An
attacker able to manipulate the local clock can extend a
transitioning key's validity, evade staleness checks, or
hide compromise-detection windows.

> [!INFORMATIVE]
> The intended end state is for the package manager to
> refuse operations when the system clock is plausibly
> wrong — for example when the current time precedes the
> package manager's own recorded build timestamp, or when
> no reliable time source has reported a successful sync
> since boot. A "reliable time source" means a
> cryptographically authenticated time protocol (NTS,
> RFC 8915, or Roughtime) or agreement among several
> independent unauthenticated sources; plain NTP, being
> trivially substitutable by a network-position attacker,
> does not on its own qualify.
>
> v0.22 does not mandate this gating: the clock-dependent
> checks above assume a sane clock, and clock-sanity
> verification is a planned addition to this
> specification. Operators in environments where clock
> manipulation is a concern SHOULD ensure an
> authenticated time source is in use.

## Operator authorisation

Several points in this specification call for "operator
authorisation": signature-policy `optional` operations
(§6.5.3), downgrade (§7.2.5), recovery resolution
(§7.5.1), a maximum-trusted-age override (§6.5.4), the
`allow_insecure_transport` toggle (§6.4), a clock-state
override (§7.6.5), and trust-anchor disagreement
resolution (§7.6.4).

In v0.22, operator authorisation means a **deliberate,
explicit act by the operator**: at minimum an affirmative
confirmation, specific to the elevated action in question
and distinct from the routine prompt to proceed with an
operation. It MUST NOT be inferred, defaulted, or
auto-supplied by the package manager. The authorising act
and what it authorised MUST be recorded in the audit
stream (§7.6.3, event type `peipkg.authorisation`).

> [!INFORMATIVE]
> The intended end state binds operator authorisation
> cryptographically: a fresh, KACS-authenticated
> authorisation from a principal holding rights beyond
> the operator's routine set — carrying the transaction
> identifier, the full operation specification, a nonce,
> and a timestamp — validated by KACS rather than by the
> package manager, and emitted as an audit record
> co-signed by the authorising principal so the trail
> does not rest on the package manager's own honesty.
> This depends on KACS and KMES primitives not specified
> as of v0.22 (an asymmetric KACS-bound key, and
> event-payload signature verification). Until they
> exist, the v0.22 requirement is the deliberate, explicit
> act described above, and an implementation SHOULD NOT
> present it as the stronger guarantee.

## Build-farm trust

The `farm_id` field in the manifest's build object
(§3.3.4) and in index entries (§6.2.4) identifies the
build farm that produced a package. This specification
does not normatively constrain `farm_id` values, but
consumers MAY enforce `farm_id` constraints per
repository as defence-in-depth: e.g., for the official
Peios repository, the consumer MAY refuse to install
packages whose `farm_id` is not in a configured
allowlist of legitimate farms.

This is operational defence-in-depth, not a format-level
guarantee. A compromised build farm whose private signing
key is intact can sign packages with any `farm_id`
value; `farm_id`-based filtering protects only against
configuration mistakes (e.g., a stale farm whose key
was rotated but whose `farm_id` is still recognised) and
against an attacker who has obtained a key but not the
operational identity of the legitimate farm.

## Cross-spec coordination requirements

Several defences this chapter describes as *intended end
states* depend on mechanisms not yet specified in peer
Peios PSDs as of v0.22. These are coordination points for
future specification work, not gaps in a conformant v0.22
implementation — which uses the lighter v0.22 model
described in each case.

| Intended end state | Depends on | Status |
|---|---|---|
| Cryptographically-bound operator authorisation, co-signed into the audit stream (§7.6.6) | An asymmetric KACS-bound key primitive (PSD-004) and event-payload signature verification (PSD-008) | Not yet specified |
| A dedicated recovery-class authorisation right for recovery resolution (§7.5.1.5) | A KACS right (e.g. `SeRecoveryAuthorise`) or well-known SID, plus KACS validation of authorisation tokens (PSD-004) | Not yet specified |
| Official trust anchors at a standardised OS-image path (§7.6.4) | A future PSD covering OS-image construction | Not yet specified |
| Redundant trust-anchor source, and repository configuration, in the registry (§7.6.4, §6) | A registry namespace for peipkg state in PSD-005 / loregd | Not yet allocated |
| Reconciller-mediated `/etc/` materialisation (§7.2.2, §3.4.4) | A future reconciller-framework PSD | Not yet specified |
| Clock-sanity gating of the clock-dependent checks (§7.6.5) | No peer-spec dependency; a planned addition to this specification | Planned |

These coordination points should be addressed in future
revisions of PSD-004, PSD-005, and PSD-008, alongside the
future reconciller-framework and OS-image PSDs.

## Threats out of scope

The following threats are explicitly out of scope for
this specification, and are addressed by other Peios
subsystems or by the operator:

- **Compromise of an installing operator's KACS
  identity.** The package manager runs with the
  operator's authority (§7.6, "Privilege model"); if that
  operator's KACS state is compromised, no format-level
  defence helps. KACS's own audit and recovery mechanisms
  apply.
- **Side-channel attacks on installed binaries.**
  Spectre-class, cache-timing, and similar attacks
  against installed software are not the package
  format's concern; they are addressed by the kernel
  and by software-specific mitigations.
- **Physical attacks on storage media.** A physically
  compromised disk can have its package database or
  installed files altered offline. Hash verification at
  use time (out of this spec's scope) is the
  appropriate defence.
- **Compromise of the build farm itself.** A compromised
  build farm can sign malicious packages with trusted
  keys. Detection requires reproducible-builds
  verification by independent parties (appendix A).
- **Network-level censorship or denial-of-service**
  preventing package fetching. Operational concern.

These exclusions are honest acknowledgements, not
weaknesses to dismiss. Each is a real concern; each is
addressed elsewhere.
