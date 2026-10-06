---
title: "outcome.*"
description: "Every field the evman catalogue defines under outcome: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `outcome`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="outcome.address"></a>`outcome.address`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The user-space address that faulted when the kernel tried to copy from or
to it. Meaningful only within the faulting process's address space, and
only until that address space changes.

**Carried by:**

No event carries this field yet.

## <a id="outcome.cleanup"></a>`outcome.cleanup`

- **Type:** `str.enum`
- **Values:** `succeeded` · `failed` · `declined`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The outcome of the compensating action StrataFS took to undo part of a
failed operation, such as removing an object it had just created.
`declined` means StrataFS deliberately did not undo it, because the name
no longer referred to the object it had created and removing it could
have removed someone else's.

Both `failed` and `declined` leave an object behind in the stratum that
nothing in the merged view accounts for.

**Carried by:**

No event carries this field yet.

## <a id="outcome.data-lost"></a>`outcome.data-lost`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the outcome a record describes destroyed data, rather than only
failing to do what was asked. Set this aside from ordinary failures: a
data-losing outcome is not recovered by retrying.

**Carried by:**

No event carries this field yet.

## <a id="outcome.deferred"></a>`outcome.deferred`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a refusal was raised after the caller had already been told the
operation succeeded. A deferred refusal has nobody left to receive an
error, which is why it is recorded unconditionally rather than only for
the arrangement errors.

**Carried by:**

- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="outcome.detail"></a>`outcome.detail`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Free text about the outcome, for a person to read. Optional, and never
parsed: anything a consumer would filter on belongs in `outcome.reason` or
a field of its own. Never the output of a language's debug formatter.

**Carried by:**

- [`eventd.store.quarantined`](~peios/events/eventd/eventd-store-quarantined)
- [`peinit.config.reload.applied`](~peios/events/peinit/peinit-config-reload-applied)
- [`peinit.critical-service.failed`](~peios/events/peinit/peinit-critical-service-failed)
- [`peinit.graph.validation.failed`](~peios/events/peinit/peinit-graph-validation-failed)
- [`peinit.job.ended`](~peios/events/peinit/peinit-job-ended)
- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peinit.recovery.entered`](~peios/events/peinit/peinit-recovery-entered)
- [`peipkg.action.authorised`](~peios/events/peipkg/peipkg-action-authorised)
- [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed)
- [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed)
- [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled)
- [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded)
- [`peipkg.repository.added`](~peios/events/peipkg/peipkg-repository-added)
- [`peipkg.repository.removed`](~peios/events/peipkg/peipkg-repository-removed)
- [`peipkg.transaction.recovered`](~peios/events/peipkg/peipkg-transaction-recovered)

## <a id="outcome.errno"></a>`outcome.errno`

- **Type:** `int.errno`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The error the operation failed with, as a negative errno. Absent on
success. Present where an event records an outcome that has a specific
failure rather than only a boolean.

**Carried by:**

- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed)
- [`kacs.config.value.rejected`](~peios/events/kacs/kacs-config-value-rejected)
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted)
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started)
- [`kacs.signature.crypto.failed`](~peios/events/kacs/kacs-signature-crypto-failed)
- [`kmes.buffer.swap.failed`](~peios/events/kmes/kmes-buffer-swap-failed)
- [`kmes.config.refresh.failed`](~peios/events/kmes/kmes-config-refresh-failed)
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended)
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)
- [`ntfe.policy.rejected`](~peios/events/ntfe/ntfe-policy-rejected)
- [`peinit.event.dropped`](~peios/events/peinit/peinit-event-dropped)
- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)
- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="outcome.errno-cleanup"></a>`outcome.errno-cleanup`

- **Type:** `int.errno`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The error a compensating action failed with, when an operation failed and
its undo failed too. Read with `outcome.errno`, the error of the operation
itself: the pair is how orphaned objects come to exist. Absent when the
undo succeeded or was not attempted.

**Carried by:**

No event carries this field yet.

## <a id="outcome.errno-masked"></a>`outcome.errno-masked`

- **Type:** `int.errno`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The error an underlying step actually failed with, where StrataFS
returned a different one to the caller. `outcome.errno` holds the error
the caller saw; this field holds the one it replaced, which is usually the
one that explains the failure.

**Carried by:**

No event carries this field yet.

## <a id="outcome.fallback"></a>`outcome.fallback`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the operation took a fallback path because the mechanism it
prefers was unavailable. The operation still completed, by a slower or
coarser route.

**Carried by:**

No event carries this field yet.

## <a id="outcome.field"></a>`outcome.field`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of the structure field an error was attributed to, such as the
member of an argument structure that was out of range.

**Carried by:**

No event carries this field yet.

## <a id="outcome.invariant-violated"></a>`outcome.invariant-violated`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether an internal invariant was found broken and execution continued
anyway. A record with this set describes a state the code assumes cannot
happen, so treat whatever follows it on the same mount as suspect.

**Carried by:**

No event carries this field yet.

## <a id="outcome.offset"></a>`outcome.offset`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The byte offset within the input at which parsing failed. Read with
`outcome.field` where the input is a structure.

**Carried by:**

No event carries this field yet.

## <a id="outcome.reason"></a>`outcome.reason`

- **Type:** `str.enum`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Why the operation resolved the way it did. Each event declares its own
values: a list, or a curated subset of a `uapi/pkm/trace.h` family, which
carries codes that are never event reasons. A trace code is rendered with
the family prefix stripped and case folded, so `KACS_FSR_GRANT_DENY`
presents as `grant-deny`, and an investigation escalating from the event
stream to a live trace sees the same decision described in the same terms.

**Carried by:**

- [`authd.logon.attempted`](~peios/events/authd/authd-logon-attempted)
- [`authd.service.attested`](~peios/events/authd/authd-service-attested)
- [`authd.session.ended`](~peios/events/authd/authd-session-ended)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.config.value.rejected`](~peios/events/kacs/kacs-config-value-rejected)
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected)
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started)
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)
- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)
- [`lpsd.account.created`](~peios/events/lpsd/lpsd-account-created)
- [`lpsd.account.deleted`](~peios/events/lpsd/lpsd-account-deleted)
- [`lpsd.account.modified`](~peios/events/lpsd/lpsd-account-modified)
- [`lpsd.credential.changed`](~peios/events/lpsd/lpsd-credential-changed)
- [`lpsd.credential.verified`](~peios/events/lpsd/lpsd-credential-verified)
- [`lpsd.group.created`](~peios/events/lpsd/lpsd-group-created)
- [`lpsd.group.deleted`](~peios/events/lpsd/lpsd-group-deleted)
- [`lpsd.group.member.added`](~peios/events/lpsd/lpsd-group-member-added)
- [`lpsd.group.member.removed`](~peios/events/lpsd/lpsd-group-member-removed)
- [`ntfe.policy.rejected`](~peios/events/ntfe/ntfe-policy-rejected)
- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)
- [`peinit.boot.downgraded`](~peios/events/peinit/peinit-boot-downgraded)
- [`peinit.critical-service.failed`](~peios/events/peinit/peinit-critical-service-failed)
- [`peinit.fd-store.rejected`](~peios/events/peinit/peinit-fd-store-rejected)
- [`peinit.graph.validation.failed`](~peios/events/peinit/peinit-graph-validation-failed)
- [`peinit.graph.validation.warned`](~peios/events/peinit/peinit-graph-validation-warned)
- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)
- [`peinit.on-failure.suppressed`](~peios/events/peinit/peinit-on-failure-suppressed)
- [`peinit.recovery.entered`](~peios/events/peinit/peinit-recovery-entered)
- [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed)
- [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed)
- [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled)
- [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded)
- [`peipkg.repository.added`](~peios/events/peipkg/peipkg-repository-added)

## <a id="outcome.result-raw"></a>`outcome.result-raw`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A raw result from an internal step that was neither zero nor a valid
negative errno, recorded instead of being passed on. Deliberately not
`outcome.errno`: a value outside the errno range returned from an open
could reach the caller as a pointer to a file, so StrataFS converts it to
`EIO`, and this field holds what it caught.

**Carried by:**

No event carries this field yet.

## <a id="outcome.reverted"></a>`outcome.reverted`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a credential change the kernel had prepared was silently undone,
so that the call returned success having changed nothing. The caller is
told it worked; this is the only record that it did not.

**Carried by:**

No event carries this field yet.

## <a id="outcome.success"></a>`outcome.success`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the operation succeeded. What counts as success narrows per event;
read the event's own note before computing a rate over it.

**Carried by:**

- [`authd.logon.attempted`](~peios/events/authd/authd-logon-attempted)
- [`authd.service.attested`](~peios/events/authd/authd-service-attested)
- [`authd.session.ended`](~peios/events/authd/authd-session-ended)
- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed)
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted)
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started)
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed)
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended)
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended)
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)
- [`lpsd.account.created`](~peios/events/lpsd/lpsd-account-created)
- [`lpsd.account.deleted`](~peios/events/lpsd/lpsd-account-deleted)
- [`lpsd.account.modified`](~peios/events/lpsd/lpsd-account-modified)
- [`lpsd.credential.changed`](~peios/events/lpsd/lpsd-credential-changed)
- [`lpsd.credential.verified`](~peios/events/lpsd/lpsd-credential-verified)
- [`lpsd.group.created`](~peios/events/lpsd/lpsd-group-created)
- [`lpsd.group.deleted`](~peios/events/lpsd/lpsd-group-deleted)
- [`lpsd.group.member.added`](~peios/events/lpsd/lpsd-group-member-added)
- [`lpsd.group.member.removed`](~peios/events/lpsd/lpsd-group-member-removed)
- [`peinit.config.reload.applied`](~peios/events/peinit/peinit-config-reload-applied)
- [`peinit.graph.operation.ended`](~peios/events/peinit/peinit-graph-operation-ended)
- [`peinit.job.ended`](~peios/events/peinit/peinit-job-ended)
- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peipkg.action.authorised`](~peios/events/peipkg/peipkg-action-authorised)
- [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed)
- [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed)
- [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled)
- [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded)
- [`peipkg.repository.added`](~peios/events/peipkg/peipkg-repository-added)
- [`peipkg.repository.refreshed`](~peios/events/peipkg/peipkg-repository-refreshed)
- [`peipkg.repository.removed`](~peios/events/peipkg/peipkg-repository-removed)
- [`peipkg.transaction.recovered`](~peios/events/peipkg/peipkg-transaction-recovered)
- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)

## <a id="outcome.verdict"></a>`outcome.verdict`

- **Type:** `str.enum`
- **Values:** `pass` · `reject` · `drop`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The decision a policy engine reached, where the decision has more than two
states and `outcome.success` cannot express it. `reject` and `drop` both
refuse, and differ in whether the refusal is signalled back to the sender
or the traffic is discarded silently.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="outcome.verdict-previous"></a>`outcome.verdict-previous`

- **Type:** `str.enum`
- **Values:** `pass` · `reject` · `drop`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The verdict a flow's cached judgment held before it was judged again. Set
beside `outcome.verdict`, the pair is what tells a reload that changed a
live connection's fate, such as `pass` to `drop`, from the far commoner
re-judgment that changed nothing.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
