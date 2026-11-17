---
title: Bundles
description: The layout of a bundle, the order of the certificates it
  carries, why it can stop short of the top-level, and its size limit.
---

A **bundle** is what a file carries: a leaf, and as much of the leaf's
chain as the signer chose to include.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | `kind` is `0x03` (§7.4) |
| `cert_count` | `u8` | The number of certificates, from 0 through 17 |
| `leaf_len` | `u16` | Length of `leaf` |
| `leaf` | `u8[leaf_len]` | A leaf (§7.7) |
| certificates | Variable | `cert_count` entries, each a `u16` length and a certificate (§7.6) |

A bundle is not signed. Every object in it is.

## Order

The first certificate is the one the leaf's `issuer` names. Each later
certificate is the one the certificate before it names. A top-level, if
the bundle carries one, is the last certificate. A bundle that breaks
this order is malformed.

## Stopping short

A bundle need not carry the whole chain. Where it stops, the `issuer`
field of its last object names the next certificate, and a verifier
finds that certificate as §7.11 describes.

A signer chooses between two things:

- **A short bundle.** Each file carries its leaf and perhaps its signing
  certificate. The certificates further up are installed once and found
  by hash. A deep chain then costs each file nothing.
- **A complete bundle.** The file verifies with nothing else present, at
  a cost of about 5.3 KiB for each certificate.

A bundle MAY carry its top-level. A carried top-level is used to verify
the chain, and it is never enabled by being carried: only the trust
store enables a top-level (§7.10).

## Size

A bundle MUST NOT exceed 65,536 bytes. A verifier MUST report a larger
bundle as invalid, whatever the depth of its chain.

> [!NOTE]
> The limit is the largest value an extended attribute can hold, so
> that the same bundle fits every place a bundle is carried (§7.9).
> Depth and size are separate limits, and a chain within the depth
> limit can still be too large to carry whole.
