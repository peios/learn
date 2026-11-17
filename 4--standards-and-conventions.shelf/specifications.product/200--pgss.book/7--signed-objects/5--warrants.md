---
title: Warrants
description: How a warrant is encoded, its flags and its three types, the
  rule that a child never holds more than its parent, how an unrecognized
  warrant is treated, and the Delegate, Revoke, and Name warrants.
---

A **warrant** is a named power. A certificate holds the warrants written
into it, and a leaf requests the warrants written into it. A power that
is not written down is not held: there is no default and no implied
warrant.

A warrant only ever grants. No warrant removes a power or narrows
another warrant, and a specification that defines a warrant MUST NOT
give it such a meaning.

## Encoding

A warrant is encoded as follows.

| Field | Type | Description |
|---|---|---|
| `name_len` | `u8` | Length of `name`, from 1 through 255 |
| `name` | `u8[name_len]` | The warrant's name |
| `flags` | `u8` | Flags and type |
| `value_len` | `u16` | Length of `value` |
| `value` | `u8[value_len]` | The value, in the form its type gives |

A `name` holds only the ASCII letters, the ASCII digits, `.`, and `-`.
A name with no `.` is reserved to this chapter and to the Peios
specifications. Any other party MUST name its warrants beneath a domain
name it controls, written in reverse, as `com.example.Scanner`.

The warrants of one object are written in ascending order of `name`,
compared byte for byte, and no two have the same name.

## Flags

The `flags` byte is read as follows.

| Bits | Mask | Meaning |
|---|---|---|
| 7 | `0x80` | Allow Equal |
| 6–4 | `0x70` | Type |
| 3 | `0x08` | Must Understand |
| 2–0 | `0x07` | Reserved, zero |

**Allow Equal** says whether a child's value can equal its parent's. If
the bit is clear, the child's value MUST be strictly narrower.

**Must Understand** says what a verifier that does not recognize the
warrant's name does with it. If the bit is set, the verifier MUST report
the chain as invalid. If the bit is clear, the verifier checks the
warrant as the narrowing rule requires and gives it no other effect.

## Types

The type decides the form of the value and how one value is narrower
than another.

| Type | Name | Value |
|---|---|---|
| `0` | Set | Zero or more elements |
| `1` | Namespace | One or more names |
| `2` | Limit | One `u64` |

The enumeration is closed (§7.15). A warrant of any other type is
malformed.

A **Set** value is empty, or is elements separated by a single `00`
byte. An element is one or more bytes in the range `0x20` through
`0x7E`. No element appears twice. A Set with no elements is a plain
flag: the warrant is held or it is not.

A **Namespace** value has the form of a Set, and each element is a name:
labels of lowercase ASCII letters, digits, and `-`, joined by `.`, or
the single element `.`. A name is **within** another if the two are
equal, or if it ends with `.` followed by the other. Every name is
within `.`.

A **Limit** value is exactly 8 bytes, a `u64`.

> [!NOTE]
> The boundary matters. Under plain suffix matching `evilexample.com`
> is within `example.com`. Requiring the `.` before the suffix is what
> stops one publisher's namespace containing a stranger's. A name from
> an internationalized domain is written in its ASCII form.

## Narrowing

A certificate or leaf is the **child** of the certificate that issued
it. For every warrant a child holds, a verifier MUST find that all of
the following hold, and MUST report the chain as invalid if any does
not:

1. The parent holds a warrant of the same name.
2. The two `flags` bytes are equal.
3. The child's value is no wider than the parent's.
4. If Allow Equal is clear, the child's value is not equal to the
   parent's.

For a Set, no wider means every element of the child's value is an
element of the parent's, and equal means the two hold the same
elements. For a Namespace, no wider means every name of the child's
value is within some name of the parent's, and equal means the two hold
the same names. For a Limit, no wider means the child's number is not
greater than the parent's.

A top-level has no parent, and its warrants are not narrowed against
anything.

A verifier applies these rules to every warrant, whether or not it
recognizes the name. The rules need only the flags and the value.

> [!NOTE]
> A child that claims more than its parent is rejected, not trimmed.
> Every certificate in a valid chain therefore states what it really
> holds, and a reader does not have to intersect a chain in their head
> to learn what a signer can do.

## Warrants this chapter defines

Three warrants govern the chain itself. A leaf MUST NOT hold any of
them.

| Name | Type | Allow Equal | `flags` | Meaning |
|---|---|---|---|---|
| `Delegate` | Limit | Clear | `0x20` | How many certificates can stand between the holder and a leaf |
| `Name` | Namespace | Set | `0x90` | The names the holder's leaves can be issued under |
| `Revoke` | Set, empty | Set | `0x80` | The holder can revoke itself and what is beneath it (§7.12) |

A certificate can issue a certificate only if it holds `Delegate` with a
value of 1 or more. Because Allow Equal is clear, each certificate down
a chain holds a smaller value than its issuer or does not hold the
warrant at all. A certificate without `Delegate` issues leaves and
nothing else.

A leaf's `name` field MUST be within a name of its issuer's `Name`
warrant (§7.7). A certificate without `Name` cannot issue a leaf.

## Other warrants

Every other warrant is defined by the specification of the consumer that
acts on it. A verifier reports the warrants a leaf holds, and gives none
of them any effect of its own.
