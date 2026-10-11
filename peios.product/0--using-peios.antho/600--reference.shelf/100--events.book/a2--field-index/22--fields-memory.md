---
title: "memory.*"
description: "Every field the evman catalogue defines under memory: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `memory`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="memory.check-phase"></a>`memory.check-phase`

- **Type:** `str.enum`
- **Values:** `mmap` · `mprotect` · `enable-time-scan`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

When a memory-protection check fired. `mmap` and `mprotect` are the calls
a process makes. `enable-time-scan` is the sweep KACS makes over a
process's existing mappings when a mitigation is turned on, and what it
refuses is the mitigation, not a mapping: a refusal in that phase leaves
the process unprotected rather than short of memory.

**Carried by:**

No event carries this field yet.

## <a id="memory.protection"></a>`memory.protection`

- **Type:** `uint.flags`
- **Values:** `0x1 PROT_READ` · `0x2 PROT_WRITE` · `0x4 PROT_EXEC` · `0x8 PROT_SEM` · `0x1000000 PROT_GROWSDOWN` · `0x2000000 PROT_GROWSUP`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The protection bits a mapping call asked for: the `prot` argument to
`mmap` or `mprotect`. Write-XOR-execute refuses any request that carries
both `PROT_WRITE` and `PROT_EXEC`.

**Carried by:**

No event carries this field yet.

## <a id="memory.protection-previous"></a>`memory.protection-previous`

- **Type:** `uint.flags`
- **Values:** `0x1 PROT_READ` · `0x2 PROT_WRITE` · `0x4 PROT_EXEC`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The protection an existing mapping carried before an `mprotect`, in the
same bit encoding as `memory.protection`. Read from the mapping's own
flags, so only the read, write and execute bits are ever set. Absent on
`mmap`, which has no earlier mapping.

It matters because write-XOR-execute judges the transition, not just the
request: an `mprotect` to `PROT_EXEC` alone is refused when the mapping is
currently writable, and one to `PROT_WRITE` alone when it is currently
executable.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
