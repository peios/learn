---
title: Security Model
---

This section describes the privilege model the package
manager operates under and the audit obligations it
carries. Both are Peios-specific concerns that build on
KACS (PSD-004) and eventd (PSD-008).

## Package manager principal

The package manager runs as a KACS service principal with
specific access rights. It is NOT a Linux UID-0 process;
KACS replaces UID-based privilege entirely (PSD-004). The
package manager principal MUST hold the following access
rights at install time:

- `FILE_ADD_FILE` and `FILE_ADD_SUBDIRECTORY` on the
  parent directories of any path the package payload
  installs (`/usr/`, `/etc/`, `/var/`, `/opt/`).
- `FILE_WRITE_DATA` and `FILE_WRITE_ATTRIBUTES` on
  installed files (during atomic write+rename).
- `WRITE_DAC` on installed files when applying SD
  overrides (§3.4.7).
- `WRITE_OWNER` on installed files when applying SD
  overrides whose owner SID differs from the
  inherited owner. (Owner-SID assignment is gated by
  `WRITE_OWNER` per PSD-004 §3.3.3, distinct from
  `WRITE_DAC` which gates DACL changes.)
- `DELETE` on files being removed during uninstall
  or upgrade.
- `SeRestorePrivilege` (PSD-004 §7.2) when applying
  owner SIDs that differ from the package manager's
  own SID. The package manager invokes affected
  syscalls with `RESTORE_INTENT` set, since
  `SeRestorePrivilege` is intent-gated per PSD-004.

A package manager principal that holds these rights has
substantial system authority. The trust posture of the
package manager is therefore comparable to that of a
Linux root process: a compromised package manager can
compromise the system. KACS does not eliminate this
property; it relocates it from "anyone with UID 0" to
"the specific principal granted these rights".

> [!INFORMATIVE]
> Limiting the package manager principal's authority
> below this baseline (e.g., running it without
> `WRITE_DAC` on system directories) prevents legitimate
> installation of packages that need SD overrides. The
> spec does not attempt to constrain the principal's
> rights; instead it relies on the integrity of the
> package format (signed packages, hash verification,
> etc.) to prevent malicious content from being executed
> via the package manager's authority.

## Privilege confinement

The package manager principal MUST be confined to
privileges that installation requires. The following
constraints MUST be enforced by the system's KACS
configuration; the package format itself does not
validate them, but a conformant deployment treats
violations as security defects.

- The package manager principal MUST NOT hold
  arbitrary-code-execution privileges via mechanisms
  outside the install path. Specifically: no `kexec`,
  no kernel-module loading except via the `depmod`
  side-effect tool, no `ptrace` of unrelated processes,
  no `BPF` program loading.
- The package manager principal MUST NOT hold
  privileges over hives or registry keys outside the
  package-database scope (PSD-005). Configuration of
  installed services occurs through reconciller
  daemons, not via the package manager directly.
- The package manager principal SHOULD NOT hold network
  privileges beyond what package fetching requires
  (HTTPS to configured repository hosts on standard
  ports).

These bounds limit the blast radius of a compromised
package manager principal: even if an attacker
substitutes a malicious package and the package
manager extracts it, the damage is bounded to what the
principal can do with KACS rights on `/usr/`, `/etc/`,
`/var/`, and `/opt/`.

## Audit

Every install, upgrade, uninstall, and refresh operation
MUST emit an audit event to eventd (PSD-008). The event
MUST include at minimum:

- Operation type (install, upgrade, uninstall, refresh,
  recovery)
- Operating principal (the KACS service principal that
  invoked the package manager)
- Target package(s): name, version, architecture
- Source repository (for install/upgrade)
- Outcome (success, rejection, rollback) with
  rejection-reason if applicable
- Transaction identifier
- RFC 3339 UTC timestamp

The package manager MUST emit the event before the
operation's commit step (§7.4.5 step 2) for
transactions that succeed, and MUST emit a separate
failure event when an operation is rejected or rolled
back.

A package manager that cannot emit audit events (eventd
unavailable, audit destination unreachable) MUST refuse
the operation. Silent operations are forbidden.

### Canonical event types

Audit events emitted by the package manager MUST use
event-type strings drawn from the following set so that
eventd's per-event-type access control (PSD-008 §9) can
target peipkg events precisely:

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

### Audit ordering

Audit emission MUST follow these ordering rules with
respect to the transaction commit procedure (§7.4.5):

1. eventd reachability MUST be probed once at the start
   of any transaction, before the first per-package
   parse-and-validate step (§7.1.2.1). If eventd is
   unavailable, the transaction MUST be refused before
   any preparation work proceeds.
2. The pre-commit audit event for each operation in
   the transaction MUST be emitted before the
   commit-intent record is persisted to the
   transaction journal (§7.4.5 step 2). If audit
   emission fails before commit-intent persistence,
   the transaction MUST be rolled back.
3. If audit emission fails after commit-intent
   persistence (i.e., during or after §7.4.5 step 3),
   the transaction proceeds to completion (the commit
   is durable) and the package manager MUST emit a
   delayed audit event tagged with the original
   transaction identifier and a `delayed=true` marker
   as soon as eventd becomes reachable again. The
   package manager MUST retain the unsent event in a
   separate audit-retention journal (distinct from the
   transaction journal in §7.4.5.1) under a security
   descriptor that grants write access only to the
   package manager principal. The audit-retention
   journal entry MUST persist until eventd delivery
   succeeds.
4. Each audit-retention journal entry MUST be
   integrity-protected by an HMAC under the same
   key-binding scheme as the transaction journal
   (§7.4.5.1). Tampering with retention-journal
   entries (substitution, reordering, deletion of
   pending entries) MUST be detectable on drain.
5. On startup, the package manager MUST attempt to
   drain pending audit-retention journal entries
   before serving any new transaction. If draining
   fails (eventd still unreachable), the package
   manager MUST refuse new transactions per the
   eventd-fail-closed rule (item 1).
6. The audit-retention journal MUST be bounded. If
   pending entries exceed an operator-configured
   threshold (default: 1000 entries or 100 MiB,
   whichever is smaller), the package manager MUST
   refuse new transactions until the backlog is
   drained or explicitly cleared by an operator.
   Unbounded backlog accumulation is forbidden.

   Exception — repair operations: when the backlog
   is at the cap, the package manager MUST still
   permit operations that target system-repair
   packages (the package manager itself, eventd, the
   registry components). The repair-allowlist is
   operator-configured with a documented default
   that includes these system-critical components.
   Non-repair operations remain refused until the
   backlog is drained.

   The backlog-cap refusal MUST surface a structured
   error pointing the operator at the explicit-clear
   command and at the repair-operations allowlist.

This ordering ensures eventd unavailability is
detected at a point where the transaction can still
be safely refused, while protecting against audit
loss when eventd becomes unreachable mid-commit
(after the durable atomicity boundary, the operation
is committed regardless and the audit event is
guaranteed eventual delivery).

> [!INFORMATIVE]
> Audit events feed the operator's compliance and
> incident-response tooling. A CA-hosting Peios system
> typically has audit retention requirements (PCI-DSS,
> SOC 2, or industry equivalents) that mandate records
> of every privileged change to system state. Package
> installation is exactly such a change. Failing closed
> when audit is unavailable prevents an operator from
> losing visibility during a brief eventd outage.

## Trust anchor distribution

Trust anchors for the official Peios repository (the
trust-anchor fingerprints used for repo-add per §6.5.2)
MUST be available to the package manager from at least
two of the following sources:

- The OS image (a file installed by the base system,
  outside any package). The exact path is operationally
  defined; a future PSD covering OS-image construction
  is expected to standardise it.
- A registry key (PSD-005) populated at first boot from
  the OS image.

> [!INFORMATIVE]
> Earlier drafts of this section listed a "peinit-
> managed system file" as a third source. PSD-007
> v0.22 does not specify a mechanism for peinit to
> populate non-registry files at first boot;
> consequently the third source is removed in v0.22.
> A future coordinated update may reintroduce it
> alongside a peinit specification of the
> mechanism.

Custom-repository trust anchors are supplied by the
operator at repo-add time per §6.5.2.

When trust anchors are available from multiple sources
on a given system, the package manager MUST verify
that all sources agree byte-for-byte on the anchor
values. Disagreement between sources MUST cause the
package manager to refuse all repository operations
until an operator resolves the discrepancy.

The package manager MUST NOT auto-resolve a
disagreement. When an operator resolves the
discrepancy, the OS-image source is normatively
authoritative: an operator MUST treat the OS-image-
supplied anchor as correct and update other sources to
match before resuming operations.

When fewer than the configured number of trust-anchor
sources are reachable (e.g., booted from rescue media
with the OS-image volume not mounted), the package
manager MUST refuse all repository operations until
either the missing source(s) become reachable OR an
operator authorises proceeding (§7.6.6) and records
out-of-band-confirmation evidence per §7.6.6. The
auto-resolved "surviving sources agree" path is
explicitly forbidden when any source the
configuration declares is unavailable.

A boot context indicating rescue media (operationally
defined; typically derived from boot-loader state)
MUST set a flag the package manager observes; in that
flag's presence, the cross-source check defaults to
refuse rather than to "trust the agreeing pair".

> [!INFORMATIVE]
> Bootstrap trust is not a property of the package
> format; it is a property of the OS image and the
> initial-boot procedure. The package format relies on
> trust anchors being already present when the package
> manager first runs. The redundancy across multiple
> sources defends against trust-anchor file corruption
> or removal; the cross-source consistency check
> defends against silent substitution of one source by
> a partial-system attacker.

## Clock dependence

Several normative checks in this specification depend
on the local system clock: signing-key `valid_until`
timestamps (§6.1.4), maximum trusted age (§6.5.4),
maximum index staleness (§6.2 freshness rules), and
build provenance timestamps (§3.3.4).

The package manager MUST refuse operations when the
system clock is plausibly wrong:

- The current time MUST NOT be earlier than the
  build timestamp recorded in the package manager
  package's own manifest (§3.3.4 `build.timestamp`)
  as captured at the time of the package manager's
  install. The package manager MUST persist this
  timestamp in a location with KACS protection at
  least equal to its own binary.
- A reliable time source MUST have reported a
  successful sync since the system booted, OR the
  operator MUST have explicitly authorised operating
  with an unsynchronised clock.

The "reliable time source" MUST be either (a) a
cryptographically authenticated time protocol such as
NTS (RFC 8915) or Roughtime, or (b) at least two
*independent* unauthenticated sources whose responses
agree within 2 seconds. An unauthenticated single time
source (plain NTP) does NOT satisfy this requirement
on its own.

For the purposes of (b), "independent" means the
sources MUST be operated by distinct organisational
entities AND MUST be reached over routes that do not
share a common upstream provider that an attacker
could plausibly compromise. When fewer than three
independent unauthenticated sources are reachable,
the package manager SHOULD downgrade to "operator
must explicitly authorise" rather than auto-accept
the agreeing pair, since an attacker who knocks out
one of three sources can then influence both
remaining sources to within the bounded skew with
control of a single upstream.

> [!INFORMATIVE]
> Plain NTP can be substituted by a network-position
> attacker, who can then drift the system clock to
> extend transitioning-key validity, evade index
> staleness checks, or hide compromise-detection
> windows. Authenticated time sources or
> source-agreement bound the attacker's power over
> the local clock.

If either condition fails, the package manager MUST
surface the clock-state warning and refuse the
operation absent explicit operator authorisation.

> [!INFORMATIVE]
> An attacker who can manipulate the local clock (NTP
> tampering, virtualisation host attack, or operating a
> freshly-imaged machine before time sync) can silently
> extend the validity of a transitioning key, evade
> staleness checks, and hide reproducibility-violation
> mismatches. The clock-state check makes this an
> explicit operational concern rather than an invisible
> degradation.

## Operator authorisation

This specification refers to "operator authorisation"
in several places: signature policy `optional`
operations (§6.5.3), downgrade authorisation
(§7.2.5), recovery resolution (§7.5.1), maximum
trusted age override (§6.5.4), `allow_insecure_transport`
toggle (§6.4), clock-state override (this section),
trust-anchor cross-source disagreement resolution
(this section).

In every case, "operator authorisation" means a
deliberate act by a principal holding KACS rights
beyond those held by the package manager principal
itself. Implementation forms include:

- An interactive yes/no confirmation by an operator
  whose KACS state demonstrates the higher rights.
- A configuration file that records authorisation
  for a specific operation type, owned by a higher-
  rights principal.
- A signed authorisation token presented at operation
  invocation.

The package manager MUST record evidence of the
authorisation in its audit log (§7.6.3). The
authorisation evidence MUST also be emitted as a
separate eventd record signed by the *authorising
principal* (not by the package manager), so that the
audit trail does not depend on the integrity of the
package manager's own audit log alone. Auto-
authorisation by the package manager principal alone
is NOT operator authorisation and MUST NOT be
accepted.

For recovery resolution specifically (§7.5.1.5), the
authorisation MUST take the form of a fresh KACS-
authenticated token from the authorising principal,
validated by KACS — not a token presented to and
accepted by the package manager itself.

The signed eventd record MUST include all of the
following fields, all freshly generated for this
specific authorisation:

- The transaction identifier of the operation being
  authorised
- The complete operation specification (operation
  type plus, where applicable, target package
  name+version+architecture+repository)
- A nonce of at least 128 bits drawn from a
  cryptographically secure random source
- An RFC 3339 timestamp at the time of signing

The package manager MUST verify that all four fields
match the current operation before accepting the
record as authorisation. A signed record from a past
operation MUST NOT be accepted for a different
operation, even if the authorising principal and
authorisation type are identical.

The package manager MUST NOT accept any operator-
authorisation evidence that it itself processed and
declared valid. Validation of the authorisation MUST
be performed by KACS using the same model as
recovery resolution (§7.5.1.5): a fresh KACS-
authenticated token from the authorising principal,
validated by KACS — not a token presented to and
accepted by the package manager itself. This
prevents a compromised package-manager UI process
from fabricating "yes" responses without ever
prompting the operator.

> [!INFORMATIVE]
> Cross-spec coordination required: the signed-by-
> authorising-principal eventd record mechanism this
> section depends on is not yet specified in PSD-008
> v0.22. PSD-008's KMES emission stamps the calling
> thread's KACS GUIDs; there is no payload-level
> co-signing primitive. PSD-009 v0.22 names this
> defence as a forward-looking requirement; a future
> coordinated update to PSD-004 (asymmetric KACS-
> bound key primitive) and PSD-008 (event-payload
> signature verification) is needed before
> conformant implementation is possible. Until that
> coordinated update lands, implementers SHOULD
> approximate this defence with whatever signing
> mechanism is locally available, recognising it
> as a known gap.

### Recovery-mode authorisation bypass

When eventd is unreachable AND the operation being
authorised is one of:

- Recovery resolution (§7.5.1.5)
- Trust-anchor cross-source disagreement resolution
  (§7.6.4)
- eventd-configuration repair (specifically: install,
  upgrade, or reinstall of an eventd-providing
  package)
- Toggling `allow_insecure_transport` to enable a
  specific repo solely for the purpose of fetching
  the above repair packages

the authorising principal MAY persist the signed
authorisation to a recovery-mode-specific durable
store under a security descriptor restricted to the
authorising principal's KACS state. The package
manager MUST drain this store on the next eventd-up
startup and emit each record as a back-dated audit
event tagged with the original signing timestamp.

This bypass is limited to the named operations to
prevent it from becoming a general fail-open
escape. Routine operations (install, upgrade,
uninstall, downgrade, refresh) MUST NOT use this
bypass; they remain subject to the eventd-fail-closed
rule (§7.6.3.2 item 1).

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

Several defences specified in this chapter depend on
mechanisms not yet specified in peer Peios PSDs as of
v0.22. These are coordination points for future
specification work, not bugs in PSD-009. An
implementation conforming to PSD-009 v0.22 must
approximate these defences with whatever peer-spec
substrate is available at the time of implementation,
recognising the gap.

| PSD-009 requirement | Depends on | Status |
|---|---|---|
| "Recovery-class operator" principal (§3.4.4.1, §4.3.2, §7.5.1.5) | A new KACS privilege or well-known SID in PSD-004 | Not yet specified |
| Operator-authorisation eventd record signed by authorising principal (§7.6.6) | Asymmetric KACS-bound key primitive in PSD-004 + event-payload signature verification in PSD-008 | Not yet specified |
| Recovery-mode authorisation (§7.5.1.5, §7.6.6) | A KACS right `SeRecoveryAuthorise` or equivalent, plus KACS validation of fresh authorisation tokens | Not yet specified |
| Trust anchors via OS image at known location (§7.6.4) | A future PSD covering OS-image construction | Not yet specified |
| Reconciller-mediated `/etc/` materialisation (§3.4.4 informative) | A future reconciller-framework PSD | Not yet specified |
| Registry namespace for peipkg state (drop-in list, allowlist, trust anchors, repo configs) | Coordinated namespace allocation in PSD-005 / loregd | Not yet allocated |
| eventd reachability probe (§7.6.3) | A probe primitive in PSD-008 | Not yet specified |
| Side-effect tool allowlist signed-delta updates (§4.3.2) | Asymmetric KACS-bound key primitive in PSD-004 | Not yet specified |

These coordination points should be addressed in
future revisions of PSD-004, PSD-005, PSD-007, and
PSD-008, alongside the future reconciller and OS-image
PSDs. PSD-009 v0.22 names them as forward-looking
requirements; conformant implementation is contingent
on the named peer-spec mechanisms becoming concrete.

## Threats out of scope

The following threats are explicitly out of scope for
this specification, and are addressed by other Peios
subsystems or by the operator:

- **Compromise of the package manager principal itself.**
  If the principal's KACS state is compromised, no
  format-level defence helps. KACS's own audit and
  recovery mechanisms apply.
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
