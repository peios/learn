---
title: Enumerations
description: The values PSI defines for itself — key types, result outcomes, change scopes, capabilities, and claim value types and flags.
---

Values PSI defines for itself. Everything else it carries is PGSS
Logon's — see PGSS §2.B.

Adding a value to any enumeration here is a breaking change requiring a
version bump (§2.7). The two exceptions are the capability bitmask
below, and PGSS Logon's field bitmask, which PSI carries unchanged and
which may gain bits without one.

## Key types

Carried in a `Query` key entry's `key_type` (§2.15) as a `u8`.

| Value | Name | Key is in |
|---|---|---|
| 0 | *none* | The key entry is absent |
| 1 | `Name` | `name` |
| 2 | `Sid` | `sid` |
| 3 | `RelativeId` | `relative_id` |

Zero is not a key. It is how an `EnumerateSource` encodes an empty `of`
(§2.16), which is the only place it may appear; an encoder MUST NOT send
it in a `Query` key and a decoder MUST reject one that arrives there.

PGSS Logon's key types (PGSS §2.B) share the first two values and differ
in the third, where it carries an **absolute** POSIX identifier. The
values are not interchangeable and the tables are deliberately separate:
`3` means a rebased number on one side of the authority and a relative
one on the other, which is the whole of §2.20 expressed as a number.

## Result outcomes

Carried in a result entry's `outcome` (§2.15) and in
`EnumerateResult.outcome` (§2.16) as a `u8`.

The values are PGSS Logon's (PGSS §2.B). A source may send only these
three:

| Value | Name |
|---|---|
| 1 | `Found` |
| 2 | `NotFound` |
| 4 | `Refused` |

`Unavailable` (`3`) and `Malformed` (`5`) are the authority's to produce
and MUST NOT be sent by a source — see §2.15. A decoder MUST reject
either arriving from a source, rather than leaving the check to a
caller.

## Change scopes

Carried in `Changed.scope` (§2.17) as a `u8`.

| Value | Name |
|---|---|
| 1 | `All` |
| 2 | `Object` |

## Capabilities

Carried in `Register.capabilities` (§2.8) as a `u32` bitmask.

| Bit | Name |
|---|---|
| 0 | `QUERIES` |
| 1 | `ENUMERATES` |
| 2 | `MEMBERS` |
| 3 | `PUSHES_CHANGES` |

Unlike the enumerations above, a bit MAY be added here without a version
bump. A source that does not set a bit has not declared the capability,
and an authority MUST NOT send a message the source did not declare it
answers (§2.8) — so an authority that predates a bit simply never uses
it, and a source that predates one never sets it. Both are the safe
reading.

`MEMBERS` gates a *field* rather than a message: an authority MUST NOT
set the `MEMBERS` field bit of a `Query` (§2.15) against a source that
did not declare it.

## Claim value types and flags

A claim's `value_type` and `flags` (§2.13) are PCDS §5.9's, and are not
restated here.

They are nonetheless **closed** on this interface: a decoder MUST reject
a value type or a flag bit it does not recognise, rather than carrying
it through to an authority that will put it on a token. Adding one is
therefore a breaking change to PSI by the rule above, even though the
values themselves belong to PCDS.
