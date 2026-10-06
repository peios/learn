---
title: "access.*"
description: "Every field the evman catalogue defines under access: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `access`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="access.audit-mask"></a>`access.audit-mask`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The full continuous-audit mask cached on a handle, of which
`access.matched` is the part this operation touched. Present so an operator
can see what else on that handle would fire, which cannot be derived from
the intersection alone.

**Carried by:**

- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="access.bypass"></a>`access.bypass`

- **Type:** `str.enum`
- **Values:** `priv` · `si-fromkernel`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Why a signal was delivered with no access check at all. `priv` is a signal
the kernel sent as itself (`SEND_SIG_PRIV`); `si-fromkernel` is one whose
`si_code` marks it as kernel-originated. Either is a total bypass of the
process-access model, keyed off the signal's origin, so a spoofed origin
would be silent; absent when the signal was checked.

**Carried by:**

No event carries this field yet.

## <a id="access.decided"></a>`access.decided`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The bits the DACL evaluation reached a conclusion on, granted or denied
by an ACE. A requested bit outside this set was never mentioned by any ACE
and was denied because nothing granted it — a different finding from an
explicit deny, and one `access.granted` alone cannot show.

**Carried by:**

No event carries this field yet.

## <a id="access.default-descriptor"></a>`access.default-descriptor`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether an authorisation decision used the compiled-in default security
descriptor rather than one an administrator configured. When true, the
policy that decided was built into the kernel and is not visible anywhere
in the registry. The case that produces it today is a write to the base
layer when the base layer has no metadata row of its own.

**Carried by:**

No event carries this field yet.

## <a id="access.denied-integrity"></a>`access.denied-integrity`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The bits mandatory integrity control denied: the rights the object's
mandatory label withholds from a caller of lower integrity, whatever its
DACL says. On an access-check record these are the requested bits, or every
bit for a `MAXIMUM_ALLOWED` request, and the field is absent when there were
none.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)

## <a id="access.denied-trust"></a>`access.denied-trust`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The bits the process-trust label denied: the rights the object's trust
label withholds from a caller whose PIP does not dominate it. Read as
`access.denied-integrity` is, and can be non-zero in the same evaluation.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)

## <a id="access.disallowed"></a>`access.disallowed`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The requested bits that fall outside the set the operation permits at
all, whatever the descriptor says. Such a request is refused before any
access check.

**Carried by:**

No event carries this field yet.

## <a id="access.granted"></a>`access.granted`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The access mask in force. What that means narrows per event — the rights
this check granted, or the rights a handle was opened with — so read the
event's own note.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="access.granted-staged"></a>`access.granted-staged`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What a staged central access policy, not yet in force, would have granted.
Carried beside `access.granted`, the grant the policy in force produced;
the two differing is the record of what a policy change will alter before
it is made.

**Carried by:**

- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

## <a id="access.matched"></a>`access.matched`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The subset of the requested access that overlapped an audit mask and
therefore caused the record to exist. The bits that triggered the audit,
not the bits that were used.

**Carried by:**

- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="access.maximum-allowed"></a>`access.maximum-allowed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the request was made in `MAXIMUM_ALLOWED` mode, asking for
whatever the descriptor would grant rather than for named rights. Changes
how SACL audit ACEs match, and such a request cannot fail, so it is needed
to read both `access.granted` and `outcome.success`.

**Carried by:**

No event carries this field yet.

## <a id="access.missing"></a>`access.missing`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The rights an operation needed that the handle did not have. Carried on a
refusal of an operation on an already-open handle: the handle's
`access.granted`, and what it lacked.

**Carried by:**

No event carries this field yet.

## <a id="access.privileged"></a>`access.privileged`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the check was satisfied by a privilege rather than by the
descriptor. True on a descriptor written with `SeRestorePrivilege` over a
missing or corrupt one, which is a complete bypass of the object's access
control and not a decision the descriptor made.

**Carried by:**

No event carries this field yet.

## <a id="access.ptrace-mode"></a>`access.ptrace-mode`

- **Type:** `uint.flags`
- **Values:** `0x1 PTRACE_MODE_READ` · `0x2 PTRACE_MODE_ATTACH` · `0x4 PTRACE_MODE_NOAUDIT` · `0x8 PTRACE_MODE_FSCREDS` · `0x10 PTRACE_MODE_REALCREDS` · `0x20 PTRACE_MODE_GETFD` · `0x40 PTRACE_MODE_PIDFD_OPEN` · `0x80 PTRACE_MODE_PROC_QUERY_LIMITED` · `0x100 PTRACE_MODE_PROC_QUERY_INFORMATION`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The ptrace access mode of a cross-process check. The last four bits are
Peios additions that let KACS tell a pidfd open, a descriptor theft and a
`/proc` read apart from a generic ptrace check. The mode decides the
process right required: `PTRACE_MODE_GETFD`, taking another process's file
descriptor, needs `PROCESS_DUP_HANDLE`.

**Carried by:**

No event carries this field yet.

## <a id="access.requested"></a>`access.requested`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The access mask the caller asked for, after generic bits have been mapped to
type-specific ones. Generic bits never survive into an event.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)

## <a id="access.requested-minimum"></a>`access.requested-minimum`

- **Type:** `uint.mask`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The smallest access a POSIX open genuinely needed, before the kernel
widened the request for compatibility. Carried beside `access.requested`:
the difference is access the caller was given without asking for it.

**Carried by:**

No event carries this field yet.

## <a id="access.self"></a>`access.self`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the operation targeted the caller itself. Several cross-process
checks exempt a process acting on itself structurally — `raise()` must work
even when a restricted token would fail its own process's descriptor — so
true means no descriptor was consulted.

**Carried by:**

No event carries this field yet.

## <a id="access.vfs-mask"></a>`access.vfs-mask`

- **Type:** `uint.flags`
- **Values:** `0x1 MAY_EXEC` · `0x2 MAY_WRITE` · `0x4 MAY_READ` · `0x8 MAY_APPEND` · `0x10 MAY_ACCESS` · `0x20 MAY_OPEN` · `0x40 MAY_CHDIR` · `0x80 MAY_NOT_BLOCK`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The VFS permission mask the kernel passed to the check. A different
vocabulary from `access.requested`, which is the KACS rights the mask was
mapped to; a record carrying both shows the mapping.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
