---
title: Prior Art
description: Where PSO sits against X.509 and Authenticode, authorization
  certificates, attenuating tokens, and OpenPGP revocation, and which
  resemblances are deliberate.
---

## X.509 and code signing

The shape is the familiar one: a root, certificates that sign
certificates, and a signature on a file at the end. Three things differ
on purpose.

A leaf is a statement and not a certificate with a key, so a signing
key is never spread across every file it signs for.

Nothing expires. Code-signing systems built on X.509 need a trusted
timestamp so that a file signed while a certificate was valid stays
valid afterward, and a verifier that can trust a clock. PSO has neither
and withdraws trust by revocation alone.

What a certificate permits is written as warrants that every verifier
checks the same way, where X.509 spreads it across key usage, extended
key usage, name constraints, and policy extensions, each with rules of
its own.

## Authorization certificates

SPKI (RFC 2693) certificates carry authorizations, and a delegated
authorization can be no wider than the one it came from. Warrants are
that idea with a fixed, small set of narrowing rules, chosen so that a
verifier can enforce them for a warrant it has never heard of.

## Attenuating tokens

Macaroons and their successors let a holder narrow a credential and
pass it on, and never widen it. The narrowing rule of §7.5 has the same
direction. The difference is that a PSO chain is public and checked
against keys, and holds no shared secret.

## OpenPGP

Preparing a revocation when a key is made, and keeping it apart from
the key, is long-standing practice with OpenPGP keys (RFC 9580 defines
the revocation signature). §7.12 recommends it for the same reason: the
moment a revocation is needed is the moment the key is least likely to
be at hand.

## Design influences

**Reject, never trim.** A certificate that claims more than its issuer
is invalid. A reader of any valid certificate sees what it really
holds.

**The verifier knows no policy.** A verifier reports where a chain ends
and what its leaf holds. Which results and warrants matter is each
consumer's, so a new use of PSO needs a new warrant and no new verifier.

**Anchors are listed, never discovered.** A top-level is trusted
because the trust store holds it, and a certificate arriving with a
file can complete a chain but cannot anchor one.

**Taking away needs no permission.** A revocation and a distrust entry
can only refuse, so neither needs approval to add. Everything that
restores or grants trust does.
