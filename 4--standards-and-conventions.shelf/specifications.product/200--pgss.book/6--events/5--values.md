---
title: Values
description: The one wire form for every kind of value — binary SIDs and GUIDs, nanosecond times, real booleans, symbolic enumerations — the field types that name them, absent keys, and where this chapter departs from the shared data conventions.
---

Every value has one wire form, and the field's type names it. A payload
is one MessagePack map with string keys (PSPK §2).

## Types

| Value | Wire form | Type |
|---|---|---|
| Principal | A binary SID (PCDS) | `bin.sid` |
| GUID | The 16-byte binary GUID (PCDS) | `bin.guid` |
| LUID | Unsigned integer | `uint.luid` |
| ACE | The binary ACE (PCDS) | `bin.ace` |
| Point in time | Unsigned integer, nanoseconds since the Unix epoch | `uint.time` |
| Duration | Unsigned integer, nanoseconds | `uint.duration` |
| Size in bytes | Unsigned integer | `uint.bytes` |
| Access mask | Unsigned integer | `uint.mask` |
| Flags | Unsigned integer | `uint.flags` |
| Integrity level | Unsigned integer, the integrity RID | `uint.integrity` |
| Error number | Signed integer, negative | `int.errno` |
| Boolean | MessagePack boolean | `bool` |
| Enumeration | String, kebab-case | `str.enum` |
| Numeric enumeration | Unsigned integer | `uint.enum` |
| Path | String | `str.path` |
| IP address | String, in the textual form for its family | `str.ip` |
| Digest | Binary | `bin` |
| Text | String | `str` |
| Other integer | Unsigned or signed integer | `uint`, `int` |

An emitter MUST encode a value in the wire form of its field's type. A
consumer MUST NOT accept a different form as the same value: a SID
written as an SDDL string is not a `bin.sid`.

**Enumerations are symbolic.** An enumeration is a kebab-case string
naming the value, `wrong-type` rather than `2`. A `uint.enum` is
permitted only where the numbers are fixed by another specification or
an external standard — an impersonation level, an address family — and
a consumer renders it by name. Every enumeration declares its values in
its fragment, or names the reason-code family it draws them from, and
states whether the set is closed (§6.10). A consumer that meets a value
of an open enumeration it does not know MUST treat it as a value rather
than an error, and SHOULD show it as written.

**Masks need their kind.** A `uint.mask` is decoded against the table
for the kind of thing it applies to, which the same record names in
`object.kind`. An event that carries a `uint.mask` field MUST carry
`object.kind`.

## What an emitter does not write

- **An absent value.** A field with no value is omitted: the key is not
  written. An emitter MUST NOT write nil, an empty string or zero to
  mean "none".
- **The header again.** An emitter MUST NOT repeat in its payload a value
  the header already carries: the time, the sequence, or the emitter's
  token and process GUIDs (§6.4).
- **A name beside a SID.** A principal is carried as its SID only. An
  emitter MUST NOT carry a principal's name in a field; resolving a SID
  to a name is a consumer's convenience, done when the record is read.
- **Units in a name.** The type carries the unit. A duration is
  `operation.duration`, never `operation.duration-ns`.
- **Debugging output.** A string value MUST NOT be the output of a
  language's debug formatter. Its format is not stable and no consumer
  can rely on it.

> [!NOTE]
> Names are kept out of events because a name is not stable and a SID
> is. A principal renamed after the event would otherwise appear under
> its old name in every record written before the change, and a search
> by the new name would miss them.

## Departures from the shared conventions

This chapter departs from the data conventions of the Conventions book
§3.3 on two points:

- **Timestamps** are unsigned integers counting nanoseconds since the
  Unix epoch, not RFC 3339 strings. The record header already carries
  time this way (PSPK §2), and one form for every time in a record lets
  a consumer compare them directly.
- **Digests** are carried as binary, not lowercase hexadecimal. A
  consumer renders them as hexadecimal for display.
