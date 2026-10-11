---
title: "fields.*"
description: "Every field the evman catalogue defines under fields: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `fields`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="fields.attestation.userspace"></a>`fields.attestation.userspace`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Set on a kernel-originated record that carries a value userspace
supplied, and absent otherwise. Such a value is the supplying component's
claim: it is what the component says it enforced, which the kernel copied
but did not observe. The fields that can hold one are marked asserted in
their definitions.

A userspace-originated record never carries this field, because its
`emitter.class` already says the whole payload is the emitter's word.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
