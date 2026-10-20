---
title: Terminology
description: The nouns this chapter is specified in — event type, root, segment, field, path, role, domain, participant, fragment, tier, essential, emission policy, gating, variant and asserted field — and its notation for types and pseudocode.
---

**Event type.** The dotted name an event is written under, in the form
of §6.3. `kacs.audit.access.checked` is an event type.

**Segment.** One dot-separated part of an event type or of a field
path.

**Root.** The leading segments of an event type that name its owner: a
platform root, or a package name (§6.3).

**Platform root.** A short root reserved for one platform component,
listed in §6.A.

**Field.** One value in an event, named by its path. A field is either
in the payload or, for the header fields of §6.4, in the record header.

**Path.** The dotted name of a field. In a payload, each segment is a
map key and the path is the chain of maps leading to the value (§6.4).

**Role.** The leading segment of a path that names a participant in the
event: `subject`, `object`, `source`, `destination` or `emitter` (§6.4).

**Participant.** A party to an event that a role names: who acted, what
was acted on, where something came from or went to, and who wrote the
record.

**Domain.** The leading segment of a path that is not a role. A domain
names a property of the event itself, such as `outcome`, or a thing the
event happened within, such as a ring buffer (§6.4).

**Thing.** The segment after a role that says what kind of participant it
is: `token`, `process`, `file`, `key`.

**Variant.** A field that is another reading of a value with its own
field: the value before a change, the value asked for, the value
expected. A variant is named by a qualifier (§6.4).

**Fragment.** A file describing events and fields, in the form of §6.10.
**The catalogue** is every fragment installed on a system.

**Tier.** How much an event matters to an operator, declared per event
type: `essential`, `standard`, `verbose` or `debug` (§6.8).

**Essential.** The tier of an event that is never switched off (§6.8).

**Emission policy.** The registry tree that switches event types on and
off (§6.9).

**Gating.** What decides whether one occurrence of an enabled event type
is recorded, where something other than the emission policy decides it:
a SACL, a token's audit policy. Declared per event type in its fragment.

**Asserted field.** A field whose value, on a kernel-originated record,
may have been supplied by userspace rather than observed by the kernel
(§6.7).

Terms defined in PSPK §2 — event, header, payload, origin class,
sequence — are used here with the same meaning and are not redefined,
and nor are those of PCDS (SID, GUID, LUID, security descriptor, SACL,
ACE), those of the registry (key, value, `REG_DWORD`, `Machine\`),
which are the Peios Kernel TRM's, or package name, which is PSPU §5.3's.
*MessagePack* is the format of the MessagePack specification, version
2.0.

## Notation

### Field types

A field's type is written `storage.semantic`: how the value is stored
on the wire, then what it means. `bin.sid` is a binary SID, `uint.time` a
point in time carried as an unsigned integer. One name carries both, so
a reader knows the wire form and the rendering without a lookup. A type
followed by `[]` is an array of that type. The types are listed in §6.5.

### Pseudocode

The pseudocode in §6.9 uses the corpus conventions of the Conventions
book §2.3, and in addition:

| Notation | Meaning |
|---|---|
| `and`, `or`, `not` | Boolean operators |
| `for each x in list` | Iteration in list order |
| `absent` | No value: a key or registry value that does not exist |
| `return` | Ends the procedure with the value given |
