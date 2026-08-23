---
title: Signing Key Status and Rotation
description: What each key status means for verification, how rotation works, the offline emergency key, and what happens on compromise.
---

## Statuses

A key's `status` describes its role in the repository's current
operation.

| Status | Used for new signatures | Accepted for verification |
|---|---|---|
| `active` | yes | yes |
| `transitioning` | no | yes, until `valid_until` |
| `revoked` | no | **never**, whatever the cryptography says |

- **`active`** — the key currently signs new packages and indexes. A
  consumer MUST accept its signatures.
- **`transitioning`** — the key was active and remains acceptable for
  verification until its `valid_until` timestamp, but no longer produces
  new signatures. A consumer MUST accept its signatures while the
  current time is at or before `valid_until`, and MUST reject them
  afterwards. A `transitioning` key entry MUST carry a `valid_until`.
- **`revoked`** — the key is no longer trusted under any circumstance. A
  consumer MUST reject its signatures regardless of when they were
  produced and regardless of whether they verify cryptographically.

A status other than these three is invalid.

A repository MAY have several `active` keys, permitting parallel
signing; any number of `transitioning` keys, each with its own
`valid_until`; and any number of `revoked` keys.

`revoked` is the explicit signal of a compromise event. `transitioning`
is for routine rotation only, and the two MUST NOT be conflated.

## Retention of revoked entries

A revoked entry MUST be retained in the descriptor for at least one year
after the revocation. Removing it prematurely would hide the public
acknowledgement of compromise from consumers with stale caches.

A repository MUST continue to serve the public key file of a revoked key
for as long as its entry is retained, so that a consumer fetching the
descriptor can resolve every key it declares.

> [!NOTE]
> Keeping a revoked key in the descriptor is useful even though its
> signatures are rejected regardless: it is a public acknowledgement a
> consumer can audit, and it means a consumer encountering a signature
> from that key gets "this key was revoked" rather than a generic "key
> not in trust set".

## Rotation

A repository rotates a signing key by:

1. Generating a new key pair.
2. Adding the new public key to the descriptor's key list alongside the
   existing one.
3. Beginning to sign new content with the new key.
4. After a transition period during which both are advertised, marking
   the old key `transitioning` with a `valid_until`, and eventually
   removing it.

During the transition, content signed with either key is acceptable.
After the old key's validity lapses, only the new key's signatures
remain acceptable.

The length of the transition period is operational policy and is not
specified here. Its purpose is to give consumers time to fetch the
updated descriptor and learn the new key before old signatures stop
being honoured.

## The offline emergency key

A repository SHOULD maintain at least one **offline** active signing key
in addition to its routine signing keys. The offline key's private
material is stored separately from build infrastructure and is used only
for descriptor updates and emergency rotations.

The offline key exists to break a chicken-and-egg in compromise
response. Revoking a compromised signing key requires publishing a new
descriptor, which must itself be signed. If the only trusted key is the
compromised one, the operator must sign the revocation with the
compromised key — giving an attacker who holds that same key the ability
to substitute their own revocation that adds a key of their choosing.

With an offline key, the operator signs the descriptor update revoking
the compromised key without relying on the compromised key at all.
Consumers holding the offline key in their trust set accept the update;
consumers who do not must perform an out-of-band trust-anchor refresh
(§5.37).

> [!NOTE]
> This is SHOULD rather than MUST because the implementation question —
> hardware module, air-gapped machine, threshold custody — is the
> operator's. A future version may make it mandatory.

## Compromise

A key SHOULD be considered compromised if its private material may have
been obtained by an unauthorised party.

A compromised key MUST be marked `revoked` in the descriptor immediately
on discovery. Packages signed with it SHOULD be re-signed with a fresh
key and re-published at new revisions.

The `revoked` status is the in-band revocation channel this
specification defines. It defends at descriptor-update granularity: a
consumer that successfully refreshes learns of the revocation at once,
and a consumer caching an older descriptor retains trust in the revoked
key only until it re-syncs — a window bounded by the maximum trusted age
of §5.37.

> [!NOTE]
> A richer out-of-band mechanism — signed revocation lists, a key
> transparency log — is reserved for a future version. The combination
> of `revoked` status, a bounded maximum trusted age, and signed
> descriptor updates closes the practical compromise-response window
> without requiring separate revocation infrastructure.
>
> The corollary a consumer must not miss: **revocation only protects the
> paths that consult the trust set.** Any code path that installs a
> package without resolving its key against the repository's trust set —
> a build or image-composition path, say — is a path on which revocation
> has no effect at all.
