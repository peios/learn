---
title: "privilege.*"
description: "Every field the evman catalogue defines under privilege: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `privilege`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="privilege.authority"></a>`privilege.authority`

- **Type:** `str.enum`
- **Values:** `privilege` · `administrators`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Which rung of a privileged gate let the operation through. `privilege`
means the caller's token held the privilege the gate asks for, enabled,
and the use was marked against it. `administrators` means it did not, and
the gate fell back to the caller's enabled membership of Administrators.

The second is an authorisation by group membership rather than by
privilege. From outside the kernel the two look identical, so this field
is the only way to tell a gate passed by SeTcbPrivilege from one passed by
an administrator who never held it.

**Carried by:**

No event carries this field yet.

## <a id="privilege.contributed"></a>`privilege.contributed`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The access bits this privilege supplied to the check, intersected with what
the caller actually asked for. Distinct from `access.granted`, which is the
whole check's result rather than this privilege's part in it.

**Carried by:**

- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)

## <a id="privilege.held"></a>`privilege.held`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Whether the caller's effective token held `privilege.name`, enabled, at
the moment the gate asked. Every privilege gate tests for an enabled
privilege, so a privilege present on the token but disabled counts as not
held: false here, with the privilege visible in the token, is a caller
that did not enable it, not one that lacked it.

**Carried by:**

No event carries this field yet.

## <a id="privilege.name"></a>`privilege.name`

- **Type:** `str.enum`
- **Values:** `SeSecurityPrivilege` · `SeTakeOwnershipPrivilege` · `SeBackupPrivilege` · `SeRestorePrivilege` · `SeRelabelPrivilege`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The privilege that contributed access. Only these five can influence an
access check today, so only these five appear. The set is open because a
privilege used to satisfy a Linux capability gate is a privilege use too,
and will be recorded with `linux.cap` as its context.

**Carried by:**

- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)

## <a id="privilege.required-held"></a>`privilege.required-held`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Whether the operation the caller asked for was the privileged variant, so
that a privilege had to be spent to perform it. Several KACS operations
have an ordinary form and a privileged one — installing a primary token
for a different identity rather than the caller's own, for example — and
this says which the caller reached for.

A boolean, not a privilege name: the privilege in question is
`privilege.name`.

**Carried by:**

No event carries this field yet.

## <a id="privilege.surviving"></a>`privilege.surviving`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The subset of `privilege.contributed` that reached the final granted mask.
Empty means the privilege fired and a later layer stripped it — a
confinement, a CAAP rule, or PIP non-dominance — which is usually the more
interesting record of the two, because it shows a boundary doing its job.

**Carried by:**

- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
