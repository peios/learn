---
title: Extension
description: How PSO grows, through warrants any party can define, the
  Must Understand flag, the reserved bits and bytes, and the format
  version that closes every enumeration.
---

## Additive changes

**Warrants.** The set of warrant names is open. Any party defines a
warrant by naming it as §7.5 requires and saying what it means to the
consumers that act on it. A verifier needs no change: it narrows every
warrant by its flags and value, and reports those a leaf holds.

**Certificates and revocations.** An authority issues these without
reference to any registry. A package installs intermediaries and
revocations into the directories of §7.10 and §7.11.

## Warrants a verifier cannot ignore

A warrant that a verifier cannot safely ignore is marked Must Understand
(§7.5). A verifier that does not recognize it reports the chain as
invalid.

A specification that defines such a warrant accepts that every verifier
released before it reports chains holding the warrant as invalid, and
SHOULD set the flag only where a verifier that ignored the warrant would
reach a wrong result.

> [!NOTE]
> The flag exists so that a future need to restrict something does not
> force a format version. It is not a way to make warrants restrictive
> in general: a warrant still only grants (§7.5), and the flag says
> that a verifier has to know what is being granted.

## Changes requiring a version

Every enumeration in this chapter is closed: object kinds, key types,
certificate roles, warrant types, hash forms, and target types (§7.B).
A new value in any of them, a new field in any layout, and any change to
the hash or signature algorithms require a new format version.

A verifier MUST treat an object whose `version` it does not implement as
malformed. A file that has to verify on systems of two versions carries
what each needs; this chapter does not define how two bundles share one
file.

## Reserved space

The header's `reserved` byte and bits 2 through 0 of a warrant's `flags`
are reserved. An authority MUST write them as zero, and a verifier MUST
treat an object in which one is set as malformed.

> [!NOTE]
> Rejecting a set reserved bit is what lets a later version give it a
> meaning. A verifier that ignored the bit would accept an object whose
> meaning it had half understood.
