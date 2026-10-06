---
title: "trigger.*"
description: "Every field the evman catalogue defines under trigger: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `trigger`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="trigger.ace"></a>`trigger.ace`

- **Type:** `bin.ace`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The exact ACE that caused this record, so a consumer can identify which rule
fired. Absent when `trigger.kind` is `policy`, because no ACE was involved.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)

## <a id="trigger.fail-closed"></a>`trigger.fail-closed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a failure to write this audit record may fail the operation it
describes. True where the record is mandatory and the operation is refused
rather than left unrecorded; false where emission is best effort.

**Carried by:**

No event carries this field yet.

## <a id="trigger.file.path"></a>`trigger.file.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The path of the file that caused the record, where that is not the object
the record is about. Two cases: an operation on one object that had a side
effect elsewhere, such as the ancestor directories a copy-up materialised;
and an ancestor whose type masked the subtree the object sits in.

**Carried by:**

No event carries this field yet.

## <a id="trigger.kind"></a>`trigger.kind`

- **Type:** `str.enum`
- **Values:** `sacl` · `policy`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Why an audit record exists at all. `sacl` means an audit ACE on the object,
or in a central access policy, matched this access. `policy` means nothing
in any SACL asked for it and the calling token's own audit policy forced it.

The distinction is how volume gets diagnosed: a flood of `policy` is a
property of the token and is fixed on the token, while a flood of `sacl` is
a property of the object and is fixed on its SACL.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)

## <a id="trigger.open-audit"></a>`trigger.open-audit`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the object's SACL required the open itself to be audited. The
registry writes its key-open audit record only when this is true, so it is
the reason such a record exists.

**Carried by:**

No event carries this field yet.

## <a id="trigger.privilege-audit"></a>`trigger.privilege-audit`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the use of a privilege required its own audit record.

**Not emitted today.** The registry computes it during the open check and
carries it across to the kernel's C side, where nothing reads it, so no
privilege-use record is produced for a registry open.

**Carried by:**

No event carries this field yet.

## <a id="trigger.sacl-match"></a>`trigger.sacl-match`

- **Type:** `uint.flags`
- **Values:** `0x1 success-audit matched` · `0x2 failure-audit matched`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which flavour of audit ACE matched. No other bits are ever set. Distinct
from `trigger.kind`, which says whether a SACL was involved at all — this
says which side of one fired, and both bits can be set at once.

**Carried by:**

- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)

## <a id="trigger.stratum.index"></a>`trigger.stratum.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The position, within the mount's stack, of the stratum whose contents
blocked an operation. Present exactly when `trigger.stratum.path` is.

**Carried by:**

No event carries this field yet.

## <a id="trigger.stratum.path"></a>`trigger.stratum.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The filesystem path of the stratum whose contents blocked an operation:
the layer holding the entry that made a creation collide, a directory
non-empty, or a name the wrong type. Without it a refusal names the error
but not which layer an administrator must look in to clear it.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
