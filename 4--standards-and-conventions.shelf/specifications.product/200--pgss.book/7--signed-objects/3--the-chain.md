---
title: The Chain
description: How roots, top-level certificates, intermediaries, and a leaf
  link by hash into one chain, the limit on its depth, and why a leaf
  carries no key.
---

A chain has four kinds of member.

| Member | Signed by | Holds a key | Holds warrants |
|---|---|---|---|
| Root | Nothing | Yes | No |
| Top-level | A root, or itself | Yes | Yes |
| Intermediary | A top-level or an intermediary | Yes | Yes |
| Leaf | A top-level or an intermediary | No | Yes, as requests |

## Links

Every certificate and every leaf names its issuer in an `issuer` field of
64 bytes:

- A leaf's and an intermediary's `issuer` is the object hash of the
  certificate that issued it.
- A top-level's `issuer` is the key hash of the root that signed it, or
  the key hash of its own key if it signed itself.

A link holds when the named issuer's key verifies the signature of the
object that names it.

> [!NOTE]
> The link is to a certificate, not to a key. One key can have two
> certificates with different warrants, and a link by key would let a
> signer choose whichever was more generous after the fact.

## Roots

A verifier is built with one or more roots, each a key type and a key
(§7.4). A verifier MUST NOT accept a root from any other source, and
MUST treat every root it holds as equal: a chain that ends at any of
them is rooted.

A root's signature on a top-level says that the warrants the top-level
claims are valid. That is the whole of what a root asserts.

## Depth

A chain MUST NOT hold more than 16 intermediaries between its leaf and
its top-level. A verifier MUST report a longer chain as invalid (§7.14).

An authority SHOULD keep a chain to fewer than 6 intermediaries. The
limit is set well above that so that it does not constrain how an
authority arranges custody of its keys: an offline certificate, a
certificate for each region or product, and a signing certificate that
is replaced on a schedule are each one intermediary.

## Why a leaf holds no key

A leaf is a statement, not a certificate. An authority that signs files
already holds the key of the certificate it signs them under, so a key
for each leaf would be one more secret to protect with nothing gained.
Without a key, a leaf cannot issue anything, and a chain always ends
where a file begins.
