---
title: Leaves
description: The layout of a leaf, the two forms of content hash and when
  each is used, the name a leaf is issued under, and the warrants it
  requests.
---

A leaf states that a file has a given content hash. It is issued under a
name and requests warrants.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | `kind` is `0x02` (§7.4) |
| `hash_form` | `u8` | Which bytes `content_hash` covers (§7.9) |
| `content_hash` | `u8[64]` | The hash of those bytes |
| `issuer` | `u8[64]` | The object hash of the issuing certificate |
| `name_len` | `u8` | Length of `name`, from 1 through 255 |
| `name` | `u8[name_len]` | The name the leaf is issued under |
| `warrant_count` | `u8` | The number of warrants |
| `warrants` | Variable | That many warrants (§7.5) |
| `signature` | By the issuer's key type | Signature over every preceding byte |

## Name

A leaf's `name` says who vouches for the file. It has the form of a
Namespace name other than `.` (§7.5), and MUST be within a name of the
issuing certificate's `Name` warrant.

Unlike a certificate's name, a leaf's name is bounded by the chain, so a
consumer can rely on it: a leaf named `scanner.example.com` was issued
by an authority that its own issuers allowed to sign for `example.com`.

## Warrants

A leaf's warrants are the powers its signer asks for on behalf of the
file. They narrow against the issuing certificate as §7.5 requires, so a
leaf never holds a warrant its issuer lacks. A leaf MUST NOT hold
`Delegate`, `Name`, or `Revoke`.

A signer SHOULD request only what the file needs. A leaf that requests
every warrant its issuer holds gives each consumer more to act on than
the signer meant, and a signer that issues one certificate for many
kinds of file is the case where this matters.

## What a leaf does not hold

A leaf holds no key, no time of signing, and no period of validity. A
verifier applies no clock to any object (§7.14).

> [!NOTE]
> Signatures that expire need a trusted timestamp to keep old files
> valid after their certificate's time has passed, and they need a
> clock the verifier can believe, which a system does not have early in
> boot and which an administrator can set. Withdrawal here is explicit,
> by revocation (§7.12), and there is nothing for a clock to decide.
