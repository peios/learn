---
title: "subject.*"
description: "Every field the evman catalogue defines under subject: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `subject`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="subject.job.activation-generation"></a>`subject.job.activation-generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The activation generation of the service whose job sent a notification
message, as `object.job.activation-generation` describes it. A message
from an earlier run of a service carries an older generation.

**Carried by:**

- [`peinit.notify.errno.reported`](~peios/events/peinit/peinit-notify-errno-reported)
- [`peinit.notify.exit-status.reported`](~peios/events/peinit/peinit-notify-exit-status-reported)
- [`peinit.notify.progress.reported`](~peios/events/peinit/peinit-notify-progress-reported)
- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)
- [`peinit.notify.status.reported`](~peios/events/peinit/peinit-notify-status-reported)
- [`peinit.notify.stopping.reported`](~peios/events/peinit/peinit-notify-stopping-reported)

## <a id="subject.job.guid"></a>`subject.job.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The job whose process sent a notification message: the service's main
process, or a submitted job.

**Carried by:**

- [`peinit.notify.errno.reported`](~peios/events/peinit/peinit-notify-errno-reported)
- [`peinit.notify.exit-status.reported`](~peios/events/peinit/peinit-notify-exit-status-reported)
- [`peinit.notify.progress.reported`](~peios/events/peinit/peinit-notify-progress-reported)
- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)
- [`peinit.notify.status.reported`](~peios/events/peinit/peinit-notify-status-reported)
- [`peinit.notify.stopping.reported`](~peios/events/peinit/peinit-notify-stopping-reported)

## <a id="subject.operation.guid"></a>`subject.operation.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The peinit operation the sending job was serving when it sent a
notification message, such as the start that a readiness message
completes. Absent when the job serves none.

**Carried by:**

- [`peinit.notify.errno.reported`](~peios/events/peinit/peinit-notify-errno-reported)
- [`peinit.notify.exit-status.reported`](~peios/events/peinit/peinit-notify-exit-status-reported)
- [`peinit.notify.progress.reported`](~peios/events/peinit/peinit-notify-progress-reported)
- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)
- [`peinit.notify.status.reported`](~peios/events/peinit/peinit-notify-status-reported)
- [`peinit.notify.stopping.reported`](~peios/events/peinit/peinit-notify-stopping-reported)

## <a id="subject.pip.trust"></a>`subject.pip.trust`

- **Type:** `uint`
- **Asserted:** yes
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The PIP trust level in force for the access check. Compared for dominance:
a caller whose trust does not dominate the target's is denied before the
DACL is reached. Caller-influenced on ioctl-originated events, as
`subject.pip.type` is.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))

## <a id="subject.pip.type"></a>`subject.pip.type`

- **Type:** `uint.enum`
- **Values:** `0 None` · `512 Protected` · `1024 Isolated`
- **Set:** closed
- **Asserted:** yes
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The Protected Isolated Process type in force for the access check. Held in
process state rather than on the token, and a caller of the access-check
ioctl may supply its own value — so on ioctl-originated events this is
caller-influenced, and kernel-observed everywhere else.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))

## <a id="subject.process.executable"></a>`subject.process.executable`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The executable of the process that acted, where that is not the emitter,
resolved at exec with symbolic links followed.

**Carried by:**

No event carries this field yet.

## <a id="subject.process.guid"></a>`subject.process.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the process that acted, where that is not the emitter.
Never reused, so it identifies the actor across PID reuse and after the
process has exited.

**Carried by:**

No event carries this field yet.

## <a id="subject.process.name"></a>`subject.process.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The kernel's name (`comm`) for the process that acted, where that is not
the emitter. Lossy and truncated to 15 bytes; two processes can share a
name.

**Carried by:**

No event carries this field yet.

## <a id="subject.process.pid"></a>`subject.process.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The process ID of the process that acted, where that is not the emitter: a
daemon reporting what a client did names the client here and itself in
`emitter.process.pid`. Same meaning and same caveat as
`emitter.process.pid` — PIDs are reused, so correlate on
`subject.process.guid`.

**Carried by:**

- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)

## <a id="subject.service.name"></a>`subject.service.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The service whose job sent a notification message. The sender is
authenticated by its process, so this is the service peinit established,
not one the message claimed.

**Carried by:**

- [`peinit.notify.errno.reported`](~peios/events/peinit/peinit-notify-errno-reported)
- [`peinit.notify.exit-status.reported`](~peios/events/peinit/peinit-notify-exit-status-reported)
- [`peinit.notify.progress.reported`](~peios/events/peinit/peinit-notify-progress-reported)
- [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected)
- [`peinit.notify.status.reported`](~peios/events/peinit/peinit-notify-status-reported)
- [`peinit.notify.stopping.reported`](~peios/events/peinit/peinit-notify-stopping-reported)

## <a id="subject.token.auth-id"></a>`subject.token.auth-id`

- **Type:** `uint.luid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

The LUID of the logon session the effective token belongs to. The join key to
`kacs.session.destroyed` and to `/sys/kernel/security/kacs/sessions`, and the
way to gather every event from one sign-on.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))

## <a id="subject.token.capabilities"></a>`subject.token.capabilities`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The confinement capability SIDs (`S-1-15-3-…`) the effective token carries.
Access to an object from a confined token turns on these: a confined token
reaches only what its capabilities, as well as its user and groups, are
granted. Unrelated to Linux capabilities, which are `linux.cap`. Absent on
an unconfined token.

**Carried by:**

No event carries this field yet.

## <a id="subject.token.gid"></a>`subject.token.gid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux GID the effective token projects onto, for correlating with
Linux-side data such as file ownership and `/proc`. A projection for
interoperability, never the identity KACS decides on.

**Carried by:**

No event carries this field yet.

## <a id="subject.token.group-attributes"></a>`subject.token.group-attributes`

- **Type:** `uint.flags[]`
- **Values:** `SE_GROUP_MANDATORY` · `SE_GROUP_ENABLED_BY_DEFAULT` · `SE_GROUP_ENABLED` · `SE_GROUP_OWNER` · `SE_GROUP_USE_FOR_DENY_ONLY` · `SE_GROUP_INTEGRITY` · `SE_GROUP_INTEGRITY_ENABLED` · `SE_GROUP_RESOURCE` · `SE_GROUP_LOGON_ID`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

Per-group attribute bitmasks, positionally parallel to
`subject.token.groups`. The two arrays are always the same length, and
`groups[i]` is described by `group-attributes[i]`.

`SE_GROUP_INTEGRITY` is present for ABI parity only — mandatory integrity
control reads `subject.token.integrity`, never this flag.

The attributes are the token's as held, not as requested when the token was
made: creation derives `SE_GROUP_ENABLED` from `SE_GROUP_ENABLED_BY_DEFAULT`.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))

## <a id="subject.token.groups"></a>`subject.token.groups`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The group SIDs carried by the effective token. Access is frequently granted
through one of these rather than to the user SID directly, so a search by
principal that ignores them misses most of what that principal actually did.

Reconstructing membership as the access check sees it means applying the
check's own rule: `SE_GROUP_ENABLED` set and `SE_GROUP_USE_FOR_DENY_ONLY`
clear, for allow-side matching, read from `subject.token.group-attributes`.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peinit.operation.merged`](~peios/events/peinit/peinit-operation-merged)
- [`peinit.operation.requested`](~peios/events/peinit/peinit-operation-requested)
- [`peinit.operation.started`](~peios/events/peinit/peinit-operation-started)

## <a id="subject.token.id"></a>`subject.token.id`

- **Type:** `uint.luid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

The token's own LUID, identifying this specific token rather than the logon
session it belongs to. Correlates every event produced under one token.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))

## <a id="subject.token.impersonation"></a>`subject.token.impersonation`

- **Type:** `uint.enum`
- **Values:** `0 Anonymous` · `1 Identification` · `2 Impersonation` · `3 Delegation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

The impersonation level of the effective token. A primary token also
reports 0, so read `subject.token.type` before reading 0 as Anonymous.
An impersonation token means `subject.token` and `emitter.process`
describe different principals.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))

## <a id="subject.token.integrity"></a>`subject.token.integrity`

- **Type:** `uint.integrity`
- **Values:** `0 Untrusted` · `4096 Low` · `8192 Medium` · `12288 High` · `16384 System`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

The integrity RID of the effective token. Mandatory integrity control
compares this against the object's integrity label before the DACL is
consulted at all, so a denial here never reaches an ACE.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))

## <a id="subject.token.privileges"></a>`subject.token.privileges`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The privileges the effective token holds, as the flags of its 64-bit
privilege word from `uapi/pkm/token.h`: bit n is the privilege whose LUID
is n, so `SeDebugPrivilege` is bit 20. Holding a privilege is not the same
as using it; which are switched on is `subject.token.privileges-enabled`.

Userspace emitters that report a caller's privileges by name today will
carry this set instead.

**Carried by:**

- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peinit.operation.merged`](~peios/events/peinit/peinit-operation-merged)
- [`peinit.operation.requested`](~peios/events/peinit/peinit-operation-requested)
- [`peinit.operation.started`](~peios/events/peinit/peinit-operation-started)

## <a id="subject.token.privileges-enabled"></a>`subject.token.privileges-enabled`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which of the privileges in `subject.token.privileges` are enabled, as flags
in the same bit layout. A privilege takes part in a decision only while enabled,
so a privilege that is held but disabled here could not have been what
allowed the operation.

**Carried by:**

- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peinit.operation.merged`](~peios/events/peinit/peinit-operation-merged)
- [`peinit.operation.requested`](~peios/events/peinit/peinit-operation-requested)
- [`peinit.operation.started`](~peios/events/peinit/peinit-operation-started)

## <a id="subject.token.sid"></a>`subject.token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

The user SID of the effective token the operation ran under. Under
impersonation this is the client's SID, not that of the process doing the
work.

**Carried by:**

- [`authd.logon.attempted`](~peios/events/authd/authd-logon-attempted)
- [`authd.service.attested`](~peios/events/authd/authd-service-attested)
- [`authd.session.ended`](~peios/events/authd/authd-session-ended)
- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))
- [`lpsd.account.created`](~peios/events/lpsd/lpsd-account-created)
- [`lpsd.account.deleted`](~peios/events/lpsd/lpsd-account-deleted)
- [`lpsd.account.modified`](~peios/events/lpsd/lpsd-account-modified)
- [`lpsd.credential.changed`](~peios/events/lpsd/lpsd-credential-changed)
- [`lpsd.credential.verified`](~peios/events/lpsd/lpsd-credential-verified)
- [`lpsd.group.created`](~peios/events/lpsd/lpsd-group-created)
- [`lpsd.group.deleted`](~peios/events/lpsd/lpsd-group-deleted)
- [`lpsd.group.member.added`](~peios/events/lpsd/lpsd-group-member-added)
- [`lpsd.group.member.removed`](~peios/events/lpsd/lpsd-group-member-removed)
- [`netd.hostname.changed`](~peios/events/netd/netd-hostname-changed)
- [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended)
- [`peinit.operation.merged`](~peios/events/peinit/peinit-operation-merged)
- [`peinit.operation.requested`](~peios/events/peinit/peinit-operation-requested)
- [`peinit.operation.started`](~peios/events/peinit/peinit-operation-started)
- [`peipkg.action.authorised`](~peios/events/peipkg/peipkg-action-authorised)
- [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed)
- [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed)
- [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled)
- [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded)
- [`peipkg.repository.added`](~peios/events/peipkg/peipkg-repository-added)
- [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured)
- [`peipkg.repository.refreshed`](~peios/events/peipkg/peipkg-repository-refreshed)
- [`peipkg.repository.removed`](~peios/events/peipkg/peipkg-repository-removed)
- [`peipkg.transaction.recovered`](~peios/events/peipkg/peipkg-transaction-recovered)
- [`timed.clock.stepped`](~peios/events/timed/timed-clock-stepped)

## <a id="subject.token.type"></a>`subject.token.type`

- **Type:** `str.enum`
- **Values:** `primary` · `impersonation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`caller`](~peios/events/groups/group-caller), [`subject`](~peios/events/groups/group-subject)

Whether the effective token is a primary token or an impersonation token.
Needed beside `subject.token.impersonation`, because a primary token and
an Anonymous impersonation token both report level 0 there.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) (via [`caller`](~peios/events/groups/group-caller))
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) (via [`caller`](~peios/events/groups/group-caller))

## <a id="subject.token.uid"></a>`subject.token.uid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The Linux UID this token projects onto, for correlating a Peios event with
Linux-side audit data. A projection for interoperability, never the identity
KACS decides on.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) (via [`subject`](~peios/events/groups/group-subject))

## <a id="subject.true-token.sid"></a>`subject.true-token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The user SID of the acting thread's own token, before any impersonation.
Carried on records about impersonation, where `subject.token.sid` is the
client being impersonated and this is the server doing the impersonating.
Equal to `subject.token.sid` when the thread is not impersonating.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman`, `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
