---
title: "kacs.descriptor.rejected"
description: "The record that KACS read an object's stored security descriptor, found it corrupt, and refused to use it."
---

- **Event type:** `kacs.descriptor.rejected`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** none — every unreadable stored descriptor is recorded
- **Cardinality:** one record per occurrence

The record that KACS read an object's stored security descriptor, found it
corrupt, and refused to use it. The object is then treated as having a
descriptor nobody can satisfy, so every access to it is denied until the
descriptor is replaced by someone allowed to write one.

**This is often the only explanation for a sudden, universal denial.** A
file that everyone could open and nobody now can, with no change to its
descriptor anyone remembers making, is usually this: the stored bytes no
longer parse, whether from disk corruption, a tool writing the extended
attribute directly, or an interrupted write.

KACS records the event once per descriptor read, when the object's
descriptor cache is filled, not on every denied access that follows.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `file` today: file descriptors are the only stored descriptors KACS reads this way. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | optional | Not carried today. The descriptor is read through an anchor that has no mount, so no absolute path can be resolved at that point. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | Why the descriptor was refused. `corrupt` is the only reason today.<br><br>Values here (open set): `corrupt`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
