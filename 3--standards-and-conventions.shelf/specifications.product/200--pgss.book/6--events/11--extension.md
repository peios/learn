---
title: Extension
description: What may be added to this chapter's vocabulary without breaking a conforming emitter or consumer — new event types, fields, enumeration values and platform roots — and what needs a new version.
---

## Additive changes

The following are additive. An emitter and a consumer built to this
version behave correctly in their presence:

- A new event type, under a root its emitter owns.
- A new field, defined once in the catalogue. A consumer that does not
  know a field still reads, stores and queries it by its path.
- A new value of an open enumeration, which a consumer built to this
  version treats as a value rather than an error (§6.5).
- A new platform root in §6.A, provided it is not already in use as a
  package name's first segment and is not a top-level domain.
- A new domain of a platform component's own (§6.4).
- A new key in a fragment record. A consumer that does not know a key
  ignores it.

## Changes requiring a new version

- Renaming an event type or a field, or moving a field to another path.
  Every descriptor and every query written against the old name stops
  matching.
- Changing a field's type or wire form (§6.5).
- A new value of a closed enumeration.
- Defining a field beneath a path that is a value, or giving a value to
  a path that is a map (§6.4).
- A change to the roles, the qualifiers or the standard attributes of
  §6.4, or to the tiers of §6.8.
- A change to the policy tree's location or its resolution (§6.9).

## Reserved

The roots in §6.A are reserved to the components listed against them.
The roles and generic roots of §6.4 are this chapter's, and only the
platform fragment defines fields directly beneath them. Every other
fragment is bound by rule 5 of §6.10.

`/usr/share/evman/` is this chapter's, and so is the `.evman` extension
within it. `Machine\Generic\Events` and every key and value beneath it
are this chapter's: nothing else may keep anything there.
