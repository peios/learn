---
title: Conformance
description: The obligations of an authority, a store keeper, a verifier,
  and a consumer, gathered in one place, and what conformance leaves each
  free to do.
---

## A conforming authority

- Encodes every object exactly as its layout gives, with reserved space
  zero (§7.4, §7.15).
- Signs with pure ML-DSA and an empty context, over every byte before
  the signature (§7.4).
- Issues a certificate only while holding `Delegate`, and gives no child
  a warrant it lacks or a value wider than its own (§7.5).
- Issues a leaf only under a name within its `Name` warrant, with the
  hash form the place calls for (§7.7, §7.9).
- Names a warrant of its own beneath a domain it controls (§7.5).
- Keeps a chain within 16 intermediaries and a bundle within 65,536
  bytes (§7.3, §7.8).

## A conforming store keeper

- Enables a top-level only as §7.10 allows, and leaves a top-level that
  a package ships without a root's signature quarantined.
- Records an approval as a link, shows the certificate's name and
  warrants before the approval is given, and resolves links against the
  root it is reading (§7.10).
- Accepts a revocation only with the certificates that show it applies,
  and never removes one it has accepted (§7.12).
- Obtains approval before it removes a distrust entry (§7.13).

## A conforming verifier

- Accepts roots only from its own build, and top-levels only from the
  trust store (§7.3, §7.10).
- Finds a bundle in the order of §7.9, and does not fall back to the
  extended attribute once an ELF section header is found.
- Takes the signature algorithm from the issuer's key type (§7.4).
- Narrows every warrant, recognized or not, and reports an unrecognized
  warrant with Must Understand set as invalid (§7.5).
- Finds a certificate that is not carried only as §7.11 gives, and
  checks its hash.
- Makes the checks of §7.14 in order, applies no clock, and reports one
  of the seven results or an error.
- Returns the leaf's name and warrants, the top-level's hash, and the
  root's key hash, with the results §7.14 lists.

## A conforming consumer

- Requires Rooted for anything an administrator could not grant
  (§7.14).
- Accepts Consistent only against its own list of top-levels (§7.14).
- Decides on the leaf's name and warrants as returned, never on a
  certificate's name, and does not decode the bundle (§7.6, §7.14).

## A conforming system

- Restricts writing beneath `/lcl/policy/pso/` to its store keeper
  (§7.10).
- Has every verifier on it return the same result for the same input
  (§7.1).

## What conformance does not require

Conformance does not require a system to act on any result: what a
signed file is allowed to do is the consumer's. It does not require a
verifier to recognize any warrant but the three of §7.5, to remember
certificates between verifications, or to report why a chain is
invalid. It does not require an authority to use intermediaries, to
prepare revocations in advance, or to ship short bundles. It does not
say how a store keeper obtains approval, where it fetches revocations
from, or how a verifier is given the trust store.
