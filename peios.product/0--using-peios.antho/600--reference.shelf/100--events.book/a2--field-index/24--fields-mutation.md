---
title: "mutation.*"
description: "Every field the evman catalogue defines under mutation: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `mutation`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="mutation.sequence"></a>`mutation.sequence`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The sequence number LCS stamped on a registry mutation. Allocated from the
kernel's global monotonic counter, so sequences order writes across every
hive and source, and the higher sequence wins when two writes land in
layers of equal precedence.

The counter resumes at boot from one past the highest sequence any
registered source reports. A record's sequence is therefore comparable
with any other from the same registry, not only those from the same boot.

**Carried by:**

- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="mutation.sequence-expected"></a>`mutation.sequence-expected`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The sequence number a conditional write asserted as the value's current
one, the precondition of a compare-and-swap. The write proceeds only if
the value still carries this sequence, and fails with `cas-failed` from the
source otherwise. Absent on an unconditional write.

**Carried by:**

- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="mutation.sequence-watermark"></a>`mutation.sequence-watermark`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The next sequence number the kernel would allocate, at the moment of the
record. Every sequence legitimately stored in the registry is below it, so
a source reporting a sequence at or above the watermark is claiming a
write the kernel never allocated, which is the future-sequence check that
`lcs.source.response.rejected` records.

**Carried by:**

No event carries this field yet.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
