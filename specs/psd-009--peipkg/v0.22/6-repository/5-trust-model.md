---
title: Trust Model
---

This section defines how a consumer establishes trust in a
repository, how that trust is enforced when verifying
content, and how multiple repositories interact.

## Per-repository trust

Trust is configured per repository, not globally. Each
repository a consumer is configured with has its own:

- Set of trusted signing keys (§5.2.5).
- Signature policy (§6.5.3).
- Priority for resolution (§6.5.5).

A signature from a key trusted only for repository R is
NOT accepted on a package fetched from repository S, even
if both keys are present in the consumer's overall
configuration. This per-repository scoping is essential
for the security of multi-repository systems.

> [!INFORMATIVE]
> Without per-repository scoping, a compromised low-trust
> custom repository could publish maliciously-signed
> packages whose signatures verify against a key trusted
> for the official repository, allowing escalation from a
> low-trust to a high-trust context. Per-repository
> scoping prevents this entirely.

## Adding a repository

When a consumer adds a repository, the user MUST supply:

- The repository's `<repo-base>` URL.
- One or more expected key fingerprints (the *trust
  anchors*).
- A signature policy (§6.5.3) for this repository.

The consumer THEN performs the following:

1. Fetches `<repo-base>/repo.json` (or whatever URL the
   user supplied for the descriptor).
2. Fetches `<repo-base>/repo.json.sig`.
3. For each trust anchor fingerprint supplied by the user,
   attempts to fetch the corresponding public key from the
   conventional URL or from the URL declared in the
   descriptor's `repo.signing.keys` array.
4. Verifies `repo.json`'s signature against the trust
   anchor public keys.
5. If verification succeeds, the descriptor is trusted.
   The consumer records the descriptor's contents
   (including all signing keys) as the repository's
   initial trust state.
6. If verification fails, the consumer rejects the repo-
   add operation and reports the failure.

Trust anchors are obtained out-of-band. The official Peios
repository's trust anchors are published through the
project's website, documentation, and OS image. Custom
repositories distribute their own.

> [!INFORMATIVE]
> The trust-anchor model is a deliberate trust-on-first-use
> pattern with the trust decision made by the user, not by
> the consumer's defaults. A consumer MUST NOT add a
> repository whose signing key was learned from the
> repository itself without prior verification.

### Transcription-error defence

When the consumer presents a fetched key for the user to
confirm against the supplied trust anchor, the consumer
MUST display the fingerprint in a form designed to make
mismatches visually obvious:

- The 64-character hex fingerprint MUST be split into
  groups separated by spaces or colons (e.g., groups of
  4 characters: `1a2b 3c4d 5e6f ...`).
- The consumer MUST display the fingerprint of the
  fetched key alongside the user-supplied fingerprint
  for visual comparison before committing the trust
  state.
- The consumer MUST require explicit confirmation
  (e.g., a yes/no prompt or equivalent affirmation)
  before recording the new trust state. Auto-confirmation
  on the basis of "fingerprints matched bit-for-bit" is
  permitted only in non-interactive contexts where the
  user has pre-supplied the fingerprint via a configured
  channel.

When a repository declares multiple `active` keys in its
descriptor, the user is RECOMMENDED to supply trust
anchors for at least two of them. This provides
defence-in-depth against single-anchor transcription
errors.

## Signature policy

When adding a repository, the user supplies a signature
policy specifying how strict to be:

| Policy | Meaning |
|---|---|
| `required` | All packages and indexes MUST be signed and verify. Unsigned content from this repository is rejected. |
| `optional` | Signed content is verified; unsigned content is accepted with a per-operation warning emitted to the operator. |

The official Peios repository SHOULD be configured with
policy `required`. The consumer's default policy when
adding a new repository SHOULD be `required` unless the
user explicitly chooses otherwise.

There is no `none` (silently-accept-unsigned) policy. A
consumer that intentionally permits unsigned content MUST
do so via the `optional` policy, which always emits a
per-operation warning. This warning MUST surface to the
operator on every install, upgrade, and refresh — not
merely once per session — so a misconfigured trust state
is continuously visible.

> [!INFORMATIVE]
> The `optional` policy exists to support development
> workflows, homelab setups, and air-gapped environments
> where signing infrastructure may not be available. It
> is an explicit user choice with known security
> weakening, and the per-operation warning is the
> spec's defence against the user forgetting they
> opted in.

## Refresh

A consumer SHOULD refresh its cached repository state
periodically. A refresh MUST:

1. Fetch the current `repo.json` and its signature.
2. Verify the signature against any signing key whose
   `status` was `active` or `transitioning` in the
   previously-trusted descriptor.
3. If verification succeeds, record the new descriptor as
   the current trust state. The new descriptor's signing
   keys (with their statuses) replace the previous set.
4. Fetch the active index and verify its signature against
   the new descriptor's signing keys.
5. Optionally fetch and verify the archive index.

Failure to verify a refresh MUST cause the consumer to
retain its previous trust state and report the failure.
The previous trust state remains valid until the next
successful refresh.

> [!INFORMATIVE]
> A failed refresh might mean the repository is
> temporarily unavailable, the network is interrupted, or
> the repository's signing key was rotated and the new key
> was not in the previously-trusted set. Each is a
> distinct operational concern; the consumer surfaces the
> failure to the user but does not fall back to
> unverified state.

### Maximum trusted age

A consumer MUST track the time of the last successful
refresh per repository. When the time since the last
successful refresh exceeds the *maximum trusted age*,
the consumer MUST attempt a refresh before any install,
upgrade, or downgrade operation against that repository.
If the refresh attempt fails, the consumer MUST surface
the failure and refuse the operation unless the operator
explicitly authorises proceeding with stale trust state.

The default maximum trusted age is 30 days. The default
MAY be tuned by operator configuration; values exceeding
180 days SHOULD generate a per-operation warning so a
configuration that effectively disables the freshness
check remains visible.

> [!INFORMATIVE]
> The maximum trusted age bounds the window during which
> a compromised-but-not-yet-revoked key can be used
> against a consumer that hasn't refreshed. Without this
> bound, a long-offline consumer could trust a key
> indefinitely after rotation.

## Multiple repositories and priority

A consumer MAY configure multiple repositories. Each
configured repository has a numeric priority (a positive
integer; lower numbers are higher priority).

When a package is available from multiple repositories,
resolution selects from the highest-priority repository
that contains a satisfying candidate (§4.2.4).

A consumer's default priority assignment SHOULD give the
official Peios repository the lowest numeric priority
(highest priority). User-added custom repositories receive
priorities at the user's discretion.

## Repository removal

A consumer MAY remove a configured repository at any time.
Removal:

- Deletes the consumer's cached repository state for that
  repository.
- Removes that repository's signing keys from the trust
  set scoped to it.
- Does NOT uninstall packages already installed from that
  repository. Installed packages remain installed; their
  origin information is retained for future operations
  (upgrade, removal).

If the user reinstalls a removed repository, the trust-add
procedure (§6.5.2) is performed afresh; previous state is
not implicitly restored.

### Orphaned-trust packages

A package whose originating repository has been removed
or revoked is *orphaned*: its trust chain is no longer
verifiable by the current trust state. The package
manager MUST flag orphaned packages distinctly:

- `peipkg query` operations MUST display orphaned
  packages with a clear indicator (e.g., a warning
  marker next to the package name).
- Any operation involving an orphaned package (uninstall,
  upgrade, integrity check) MUST surface the orphan
  state to the operator and recommend audit before
  proceeding.
- Upgrades to an orphaned package MUST be refused unless
  a currently-trusted repository now claims the package
  (e.g., the operator has added a replacement repo and
  the new repo's package matches the orphan's name).

Operators encountering orphaned packages SHOULD audit
them: verify the installed files' hashes against
trustworthy out-of-band records, and consider reinstalling
or removing the package via a currently-trusted
repository.

> [!INFORMATIVE]
> Orphaned packages indicate either intentional repo
> removal (e.g., decommissioning a custom repo) or a
> compromise event (the repo was revoked because its
> keys were stolen). The package manager cannot
> distinguish these automatically; surfacing the state
> lets the operator make the call.

## Cross-repository conflicts

When two configured repositories both publish packages with
the same name, no conflict exists at the format level. The
consumer resolves which version to install per the
priority rule (§6.5.5).

When two configured repositories publish packages with
overlapping `provides` namespaces or `replaces` relations,
the priority rule applies similarly: the higher-priority
repository's claim wins.

A repository operator who publishes a `provides` for a
name that conflicts with the official repository's package
SHOULD document this clearly. Consumers SHOULD warn when a
custom repository's `provides` shadow an official-repo
package.

A consumer MUST require explicit operator confirmation
before applying a `replaces` (§4.1.5) relation declared
by a non-official repository against a package originally
installed from a higher-priority repository. A custom
repository silently replacing an official-repo package
is a real escalation path; the explicit confirmation
prevents this from happening as a side effect of a
routine `peipkg upgrade` operation.

The same explicit-confirmation requirement applies when
a `conflicts` (§4.1.2) declaration from a non-official
repository would cause cascade-removal of a package
originally installed from a higher-priority repository.
A low-trust repository's `conflicts` against a
high-trust package is a denial-of-availability vector;
the explicit confirmation prevents installation of a
low-trust package from silently uninstalling a
high-trust one as a cascade side effect.

## Compromise response

If a repository's signing key is suspected of being
compromised, the consumer SHOULD:

1. Disable the repository immediately (do not fetch from
   it until the situation is resolved).
2. Audit installed packages from that repository for
   tampering.
3. After the repository operator publishes a new descriptor
   with the compromised key removed, perform a fresh trust-
   add operation with new trust anchors.

This specification does not define an automated revocation
mechanism in v0.22. Compromise response is operational.
