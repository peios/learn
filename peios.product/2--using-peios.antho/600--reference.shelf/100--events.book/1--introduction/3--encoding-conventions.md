---
title: Encoding Conventions
description: Every payload is a MessagePack map of nested maps, one per path segment — absent rather than nil, kebab-case enumerations, negative errno, and the evman catalogue as the definition of every name.
---

Every KMES payload in this book is a **MessagePack map with UTF-8 string
keys**. What may appear in it, and what each value means, is defined by
the evman catalogue; the rules below are how the catalogue's definitions
become bytes (PGSS §6.4 and §6.5).

## The catalogue is the definition

Every event type and every field is defined once, in a `.evman`
fragment installed in `/usr/share/evman/` (PGSS §6.10). An emitter
writes no field the catalogue does not define, and this book's event
pages and field index are generated from the same fragments.

To read a definition on a running system, use
[evman](~peios/event-tools/evman): `evman kacs.audit.access.checked`
prints an event type, `evman subject.token.sid` a field, and
`evman kacs.audit` everything beneath a prefix.

## Names

An event type reads as who wrote it, what it is about, and what
happened: `<root>.<noun>[.<noun>…].<verb>`, all lowercase kebab-case,
ending in a past-tense verb. `kacs.audit.access.checked` and
`stratafs.file.copied-up` are event types (PGSS §6.3).

A field is named for the part it plays, then what it is, then which
property of it the value is: `subject.token.sid`, `object.file.path`,
`outcome.success` (PGSS §6.4).

## A path is nested maps

A field's path is the chain of keys that leads to its value. Each
segment is one map:

```text
subject.token.sid   is   { "subject": { "token": { "sid": <bin> } } }
```

No key contains a `.`. A key `"subject.token.sid"` at the top level of a
payload is a different field from `subject.token.sid`, and not one any
consumer looks for.

A path is either a value or a map, never both. `access.granted` is a
value, so nothing is ever defined beneath it, and its variants are its
siblings: `access.granted-staged`, not `access.granted.staged`.

## Absent, not nil

A field with no value is **omitted**: the key is not written. An emitter
never writes nil, an empty string or zero to mean "none". A field whose
event page says `when outcome.success == false` is simply not in a
record that succeeded.

## Value representations

A field's type, given on its event page and in the field index, names
its wire form.

| Type | Wire form |
|---|---|
| `bin.sid` | **bin** holding the binary SID. |
| `bin.guid` | **bin**, exactly 16 bytes. |
| `bin.ace` | **bin** holding the binary ACE, copied from the descriptor. |
| `bin` | **bin**: a digest or other opaque bytes. Shown as hexadecimal. |
| `uint.luid` | **uint**. |
| `uint.time` | **uint**, nanoseconds since the Unix epoch. |
| `uint.duration` | **uint**, nanoseconds. |
| `uint.bytes` | **uint**, a size in bytes. |
| `uint.mask` | **uint**, an access mask, decoded against the table for the record's `object.kind`. |
| `uint.flags` | **uint**, a set of bits the field's definition names. |
| `uint.integrity` | **uint**, the integrity RID. |
| `uint.enum` | **uint**, where the numbers are fixed by another specification. Rendered by name. |
| `int.errno` | **int**, a negative error number. |
| `bool` | **bool**. |
| `str.enum` | **str**, a kebab-case name. |
| `str.path` | **str**, a path. |
| `str.ip` | **str**, an address in the textual form for its family. |
| `str` | **str**, UTF-8 text. |
| `uint`, `int` | **uint** or **int**. |

A type ending `[]` is an array of that type. Arrays that describe the
same items are parallel: `subject.token.group-attributes[i]` describes
`subject.token.groups[i]`.

Binary SIDs, GUIDs and ACEs are carried as bytes rather than as text
because they are compared as bytes. A principal is carried as its SID
only, never with its name beside it: a name is resolved when the record
is read.

## Enumerations are kebab-case words

An enumeration is a string naming the value — `wrong-type`, not `2`.
Each one's values are listed in its definition, or by the event that
carries it, together with whether the set is **closed**. A value of an
open enumeration that a consumer does not recognise is a value, not an
error.

A `uint.enum` is used only where the numbers are fixed elsewhere — an
impersonation level, an address family, `emitter.class` — and a consumer
shows it by name.

## Errors are negative errno

`outcome.errno` is the negative error number the operation returned:
`-13` for `EACCES`. It is omitted on success. Why an action failed, as a
word, is `outcome.reason`; whether it succeeded at all is
`outcome.success` (PGSS §6.6).
