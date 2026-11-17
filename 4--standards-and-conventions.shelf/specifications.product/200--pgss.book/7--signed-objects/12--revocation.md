---
title: Revocation
description: The layout of a revocation, who can revoke what, why a
  revocation needs no root and no list signer, and how a store keeper
  accepts and keeps one.
---

A **revocation** is the act of an authority: a signed object that
withdraws a certificate or a leaf.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | `kind` is `0x04` (§7.4) |
| `target_type` | `u8` | `0x01` for a certificate, `0x02` for a leaf |
| `target` | `u8[64]` | The object hash of what is revoked |
| `signer` | `u8[64]` | Who signed the revocation |
| `signature` | By the signer's key type | Signature over every preceding byte |

The `target_type` enumeration is closed (§7.15).

## Who can revoke

A revocation applies to a chain when its `target` is a member of the
chain and its `signer` is one of the following:

- **The target itself**, where the target is a certificate that holds
  `Revoke`. `signer` is the target's object hash.
- **A certificate above the target in the chain** that holds `Revoke`.
  `signer` is that certificate's object hash.
- **The root that signed the chain's top-level**, where the target is
  that top-level. `signer` is the root's key hash.

In each case the signature MUST verify under the signer's key. A
revocation that meets none of these does not apply, and a verifier MUST
ignore it.

Authority to revoke comes from standing above the target in its own
chain, and from nothing else. A revocation does not have to end at a
root. An authority whose top-level is self-signed revokes within its
own chain exactly as any other does.

> [!NOTE]
> A revocation can only take trust away, and only from what the signer
> issued or stands above. That is why it needs no vouching: an
> authority cannot reach a chain it is not part of. It is also why the
> set of revocations needs no signer of its own. Each entry proves
> itself, so any party can collect and pass them on.

## Effect

A chain with a revoked member is refused (§7.14). Revoking a certificate
refuses every chain that passes through it, including every signature it
ever made: no object carries a time, so a revocation cannot be limited
to signatures made after some moment.

An authority that wants to limit the reach of a compromise SHOULD
replace its signing certificate on a schedule, so that revoking one
refuses only what that certificate signed.

A revocation stays in effect if its signer is later revoked.

## Preparing a revocation in advance

An authority SHOULD sign a revocation for each certificate when the
certificate is made, and keep it apart from the key. Revoking then
means publishing a file, with no need for a key that might be offline,
lost, or in the wrong hands.

## Accepting and keeping revocations

A store keeper takes revocations from `/usr/share/pso/revocation/` and
from any source it is configured to fetch from. It MUST accept a
revocation only when it holds, or is given with the revocation, the
certificates that show the revocation applies, and MUST then keep it in
`/lcl/policy/pso/revocation/`.

A store keeper MUST NOT remove a revocation it has accepted, including
when the package or source that supplied it withdraws it.

> [!NOTE]
> The attack on revocation is removal, not addition. An entry that
> arrives can only refuse something its signer was entitled to refuse.
> An entry that disappears restores trust in something its authority
> withdrew. A store keeper therefore needs no approval to add one and
> has no operation to remove one.

Accepting a revocation needs no approval from the administrator.
