---
title: Establishing Trust in a Repository
description: Trust is configured per repository and never globally — adding one, guarding a mistyped fingerprint, signature policy and refresh.
---

Trust is configured **per repository**, never globally. Each repository a
consumer is configured with has its own trusted signing keys (§5.29),
its own signature policy, and its own priority.

## Adding a repository

To add a repository, the operator supplies its `<repo-base>` URL, one or
more expected key fingerprints — the **trust anchors** — and a signature
policy.

The consumer then:

1. Fetches `<repo-base>/repo.json` and `<repo-base>/repo.json.sig`.
2. Fetches the public key for each supplied anchor fingerprint, from the
   conventional URL or from the URL the descriptor declares, and
   verifies each fetched key against the fingerprint that named it
   (§5.29).
3. Verifies the descriptor's signature against those anchor keys **and
   only those**.
4. On success, records the descriptor's contents — including every
   signing key and status — as the repository's initial trust state.
5. On failure, rejects the add and reports why.

A consumer MUST NOT add a repository whose signing key it learned from
the repository itself without prior verification against an anchor.
Trust anchors are obtained out of band: through a project's website,
its documentation, or the operating system image.

> [!NOTE]
> Step 2 necessarily issues requests derived from an unverified
> document, since the descriptor is what names the key URLs. A consumer
> SHOULD limit those requests to the keys matching the supplied anchors,
> and MUST NOT follow a key URL for a fingerprint the operator did not
> name — otherwise a substituted descriptor can direct the consumer to
> fetch from arbitrary hosts before anything has been verified.

## Guarding against a mistyped fingerprint

When presenting a fetched key for confirmation, a consumer MUST:

- display the 64-character fingerprint in groups separated by spaces or
  colons — conventionally four characters per group, as
  `1a2b 3c4d 5e6f ...`;
- display the fetched key's fingerprint **alongside** the one the
  operator supplied, for visual comparison, before recording any trust
  state;
- require explicit confirmation before recording. Automatic confirmation
  on the basis of a bit-for-bit match is permitted only in a
  non-interactive context where the operator pre-supplied the
  fingerprint through a configured channel.

When a repository declares several `active` keys, the operator is
RECOMMENDED to supply anchors for at least two of them, as
defence-in-depth against a single mistyped anchor.

A consumer MUST report an anchor mismatch by naming both the anchor the
operator supplied and the fingerprints the descriptor actually declares.
A mismatch is most often a transcription error, and that is precisely
the diagnostic needed to find one.

## Signature policy

| Policy | Meaning |
|---|---|
| `required` | Every package and index MUST be signed and verify. Unsigned content from this repository is rejected. |
| `optional` | Signed content is verified. Unsigned content is accepted with a per-operation warning. |

These are the only two policies. There is no silently-accept-unsigned
policy: a consumer intentionally permitting unsigned content does so
through `optional`, which always warns.

The warning MUST surface on **every** install, upgrade, and refresh that
accepts unsigned content — not once per session — so that a
misconfigured trust state stays continuously visible.

A consumer's default policy for a newly added repository SHOULD be
`required` unless the operator explicitly chooses otherwise, and the
official repository SHOULD be configured `required`.

`optional` means signed content **is** verified. A consumer MUST NOT
treat the absence of trust anchors as licence to stop verifying: a
repository under `optional` that publishes signatures MUST have them
verified, and one that publishes none MUST produce the warning rather
than a fetch error.

> [!NOTE]
> The two failure modes here are mirror images and both are real. A
> consumer that demands a signature file under `optional` cannot add a
> repository that §5.31 explicitly permits to publish none. A consumer
> that stops verifying entirely because no anchors were configured
> leaves a repository fully substitutable by anyone on the network path,
> permanently, even after it starts publishing good signatures.

## Refresh

A consumer SHOULD refresh its cached repository state periodically. A
refresh MUST:

1. Fetch the current descriptor and its signature.
2. Verify the signature against any key whose status was `active` or
   `transitioning` in the **previously trusted** descriptor.
3. On success, record the new descriptor as the current trust state,
   replacing the previous key set with the new one.
4. Fetch the active index and verify it against the new descriptor's
   keys, applying §5.34.
5. Optionally fetch and verify the archive index, applying §5.34 to it
   as well.

A failed refresh MUST leave the previous trust state in place and be
reported. A consumer MUST NOT fall back to unverified state.

> [!NOTE]
> A failed refresh may mean the repository is unavailable, the network
> is interrupted, or the signing key was rotated to one the previously
> trusted set does not contain. These are distinct operational concerns;
> the consumer surfaces the failure and lets the operator distinguish
> them.

## Maximum trusted age

A consumer MUST track the time of the last successful refresh per
repository. When that exceeds the **maximum trusted age**, the consumer
MUST attempt a refresh before any install, upgrade, or downgrade against
that repository. If the attempt fails, the consumer MUST report the
failure and refuse the operation, unless the operator explicitly
authorises proceeding on stale trust state.

The default maximum trusted age is **30 days**. It MAY be tuned by
operator configuration; a value above 180 days SHOULD produce a
per-operation warning, so that a configuration effectively disabling the
check stays visible.

> [!NOTE]
> The maximum trusted age bounds the window in which a
> compromised-but-not-yet-revoked key can be used against a consumer
> that has not refreshed. Without it, a long-offline consumer trusts a
> rotated key indefinitely.

## Priority

A consumer MAY configure several repositories. Each has a numeric
priority: a positive integer, where a **lower number is a higher
priority**.

A consumer's default assignment SHOULD give the official repository the
lowest number. Other repositories receive priorities at the operator's
discretion.

## Removal

A consumer MAY remove a configured repository at any time. Removal
deletes the cached state and the trust set scoped to that repository. It
does **not** uninstall packages already installed from it; those remain
installed, and their origin is retained.

Re-adding a removed repository performs the full trust ceremony afresh;
previous state is not implicitly restored.

## Orphaned packages

A package whose originating repository has been removed or revoked is
**orphaned**: its trust chain is no longer verifiable by the current
trust state. A consumer MUST:

- display an orphaned package with a clear indicator in query output;
- surface the orphan state on any operation involving it, and recommend
  an audit before proceeding;
- refuse an upgrade to an orphaned package unless a currently trusted
  repository now claims it by name.

A consumer MUST NOT treat an unknown origin as an *absent* origin.
Wherever this chapter gates an operation on the relative priority of two
repositories, an orphaned package's origin MUST be treated as at least
as trusted as any configured repository, so that the gate still fires.

> [!NOTE]
> The failure this prevents is subtle and severe: a repository removed
> *because its keys were stolen* leaves packages behind whose origin no
> longer resolves. If an unresolvable origin is quietly treated as
> lowest-priority, every cross-repository guard below stops firing for
> exactly those packages — so revoking a repository would *lower* the
> protection on what it left behind, and any newly added low-trust
> repository could take an orphaned ex-official package over without
> confirmation.

Operators meeting an orphaned package SHOULD audit it: verify the
installed files' hashes against trustworthy out-of-band records, and
consider reinstalling or removing it through a trusted repository.

## Between repositories

When two configured repositories publish a package of the same name, no
conflict exists at the format level; the consumer resolves which to
install by priority. The same applies to overlapping `provides` or
`replaces` relations: the higher-priority repository's claim wins.

An operator publishing a `provides` that shadows a package of the
official repository SHOULD document it clearly, and a consumer SHOULD
warn when a lower-priority repository's `provides` shadows a
higher-priority package.

Two guards require explicit operator confirmation, and neither may be
satisfied by a general "proceed" affirmation:

- Applying a `replaces` declared by a lower-priority repository against a
  package originally installed from a higher-priority one. A repository
  silently replacing a more-trusted package is a real escalation path,
  and confirmation stops it happening as a side effect of a routine
  upgrade.
- Applying a `conflicts` declared by a lower-priority repository that
  would cause the cascade-removal of a package from a higher-priority
  one. That is a denial-of-availability vector, and confirmation stops a
  low-trust install from silently uninstalling a high-trust package.

A consumer that resolves a conflict by rejecting the plan outright,
rather than by cascading removals, satisfies the second guard vacuously.

## Compromise response

If a repository's signing key is suspected of compromise, a consumer
SHOULD disable the repository immediately, audit the packages installed
from it for tampering, and, once the operator has published a new
descriptor with the compromised key removed, perform a fresh trust-add
with new anchors.

This version defines no automated revocation mechanism beyond the
`revoked` key status (§5.32). Compromise response is operational.
