---
title: "caap.*"
description: "Every field the evman catalogue defines under caap: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `caap`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="caap.phase"></a>`caap.phase`

- **Type:** `str.enum`
- **Values:** `effective-sacl` · `staged-sacl`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Which phase of a central access policy's audit evaluation a CAAP
diagnostic describes. `effective-sacl` is a rule's SACL in the policy in
force, whose audit records are real. `staged-sacl` is the SACL of a rule's
staged, not-yet-effective version, evaluated alongside it only so that an
administrator can see what rolling it out would do; a failure there
changes nothing about the access or its audit.

Absent on a diagnostic about the whole check rather than one rule's SACL,
such as a disagreement between the staged and effective results.

**Carried by:**

- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)

## <a id="caap.policy.sid"></a>`caap.policy.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The SID identifying a central access policy. An object's SACL names the
policies that apply to it by this SID, and the kernel's policy cache is
keyed on it, so it ties a record to the policy an administrator
installed. It identifies a policy, never a user or group, even though it
has the form of a SID.

**Carried by:**

- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)

## <a id="caap.rule.index"></a>`caap.rule.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The zero-based position of a rule within the central access policy named
by `caap.policy.sid`. Meaningful only against the policy as it stood when
the record was made: replacing a policy's specification replaces its rule
list, so an index in an older record can point at a different rule today.

**Carried by:**

- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)

## <a id="caap.staged-differs"></a>`caap.staged-differs`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Whether evaluating the staged policies gave a different result from the
effective ones for this access check. True when the staged grant differs
from the effective grant, when the per-object results of an object-type
check differ, or when the staged audit records differ from those actually
produced.

A difference changes nothing about the access itself, which the effective
policies decided. It is the signal that promoting the staged policy would
change the outcome for this subject and object.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
