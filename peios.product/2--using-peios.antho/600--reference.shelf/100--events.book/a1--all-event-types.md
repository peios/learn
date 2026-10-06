---
title: "All Event Types"
description: "Every event type the evman catalogue defines, in one table: its tier, its defining fragment and its one-line summary, generated from the fragments."
---

Every event type in the evman catalogue, generated from the fragments by `pkm/tools/gen-events-book.py`: 100 event types and 593 fields, from `kacs.evman`, `kernel.evman`, `kmes.evman`, `lcs.evman`, `ntfe.evman`, `stratafs.evman`, `peinit.evman`, `peipkg.evman`, `eventd.evman`, `authd.evman`, `lpsd.evman`, `timed.evman`, `netd.evman`, `trustd.evman`.

The tier sets whether an event type is recorded by default (PGSS <span>§</span>6.8). Each type links to its page; each page's fields link to the field index.

## Access and Identity Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) | essential | `kacs.evman` | The record that an access check completed, and what it decided. |
| [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed) | essential | `kacs.evman` | The record that a caller changed, or was authorised to change and failed to change, the security descriptor of a file, a token, a process or a System V IPC object. |
| [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) | essential | `kacs.evman` | The record of what was done with a handle after it was opened. |
| [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) | essential | `kacs.evman` | The record that a privilege was spent. |
| [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed) | essential | `kacs.evman` | The record that a central access policy was installed, replaced or removed. |
| [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) | standard | `kacs.evman` | The record that a central access policy rule's SACL could not be parsed or evaluated, so the audit it asked for was skipped. |
| [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) | standard | `kacs.evman` | The record that a staged central access policy would have decided an access differently from the policy in force. |
| [`kacs.config.value.rejected`](~peios/events/kacs/kacs-config-value-rejected) | essential | `kacs.evman` | The record that KACS read one of its registry-held tables, rejected it, and carried on with what it had. |
| [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) | standard | `kacs.evman` | The record that KACS read an object's stored security descriptor, found it corrupt, and refused to use it. |
| [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted) | verbose | `kacs.evman` | The record that a thread stopped impersonating and acts as its own token again. |
| [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started) | standard | `kacs.evman` | The record that a thread took on, or tried to take on, a client's identity by impersonating its token. |
| [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed) | essential | `kacs.evman` | The record that a filesystem's KACS mount policy was set: what happens to an object on it that has no stored descriptor. |
| [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed) | essential | `kacs.evman` | The record that a logon session ended because its last token went away. |
| [`kacs.signature.crypto.failed`](~peios/events/kacs/kacs-signature-crypto-failed) | essential | `kacs.evman` | The record that the machinery for verifying signed executables cannot run. |

## Filesystem Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up) | standard | `stratafs.evman` | The record that StrataFS materialised an object into a writable stratum, successful or not. |
| [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused) | standard | `stratafs.evman` | The record that a mutation was refused because of how the mount is arranged, rather than because of an access check. |

## Registry Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended) | essential | `lcs.evman` | The record that a registry subtree backup finished, successfully or otherwise. |
| [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started) | essential | `lcs.evman` | The record that a registry subtree backup began, emitted **before any data is read**. |
| [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created) | essential | `lcs.evman` | The record that a registry key was created. |
| [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted) | essential | `lcs.evman` | The record that a registry key was deleted from a layer through its own handle, or that an attempt failed. |
| [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed) | essential | `lcs.evman` | The record that a registry key's security descriptor was changed through a key handle, or that an attempt failed. |
| [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden) | essential | `lcs.evman` | The record that a registry key was hidden in a layer through its own handle, or that an attempt failed. |
| [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) | essential | `lcs.evman` | The record that a registry key was opened and what access the open received. |
| [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned) | essential | `lcs.evman` | The record that a key's blanket tombstone was set or cleared in a layer, or that an attempt failed. |
| [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) | essential | `lcs.evman` | The record that a registry subtree restore finished, successfully or otherwise. |
| [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) | essential | `lcs.evman` | The record that a registry subtree restore began, emitted **before any state is modified**. |
| [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed) | essential | `lcs.evman` | The record of how a registry transaction ended, written for a transaction that staged at least one write some other record covers. |
| [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted) | essential | `lcs.evman` | The record that a registry value was deleted through a key handle, or that an attempt to delete one failed. |
| [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set) | essential | `lcs.evman` | The record that a registry value was written through a key handle, or that an attempt to write one failed. |
| [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected) | essential | `lcs.evman` | The record that LCS read one of its own configuration values, rejected it, and carried on with what it had. |
| [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected) | essential | `lcs.evman` | The record that LCS rejected data a registry source sent it. |

## Event Stream Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`kmes.buffer.swap.failed`](~peios/events/kmes/kmes-buffer-swap-failed) | standard | `kmes.evman` | The record that KMES could not resize its per-CPU ring buffers and kept the capacity it had. |
| [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied) | standard | `kmes.evman` | The record that KMES read its configuration key and committed what it found. |
| [`kmes.config.refresh.failed`](~peios/events/kmes/kmes-config-refresh-failed) | essential | `kmes.evman` | The record that KMES could not read one of its configuration keys and kept running on what it had. |
| [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected) | essential | `kmes.evman` | The record that KMES read a configuration value, rejected it, and carried on with what it had. |

## Network Policy Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`ntfe.policy.published`](~peios/events/ntfe/ntfe-policy-published) | standard | `ntfe.evman` | The record that a new generation of traffic rules went into force. |
| [`ntfe.policy.rejected`](~peios/events/ntfe/ntfe-policy-rejected) | essential | `ntfe.evman` | The record that the kernel read a traffic policy and refused it, so the policy an administrator wrote is **not the policy in force**. |
| [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported) | essential | `ntfe.evman` | The record of a traffic policy decision that a rule explicitly asked to be reported. |

## Service Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`peinit.boot.downgraded`](~peios/events/peinit/peinit-boot-downgraded) | essential | `peinit.evman` | A full boot was downgraded to safe mode: the machine is running a reduced service set. |
| [`peinit.cgroup.leaked`](~peios/events/peinit/peinit-cgroup-leaked) | standard | `peinit.evman` | A cgroup could not be reclaimed: its processes do not respond to the kernel, and the cgroup is leaked. |
| [`peinit.config.reload.applied`](~peios/events/peinit/peinit-config-reload-applied) | standard | `peinit.evman` | A configuration reload ran: from now on the registry as it then stood is the running configuration, or, if it failed, nothing changed. |
| [`peinit.config.reload.deferred`](~peios/events/peinit/peinit-config-reload-deferred) | verbose | `peinit.evman` | A configuration reload during the boot window changed definitions of services the boot plan had not yet launched. |
| [`peinit.critical-service.failed`](~peios/events/peinit/peinit-critical-service-failed) | essential | `peinit.evman` | A service marked Critical failed, and peinit took the machine to its reboot final action. |
| [`peinit.event.dropped`](~peios/events/peinit/peinit-event-dropped) | essential | `peinit.evman` | The ring refused one of peinit's events, and it is gone. |
| [`peinit.fd-store.rejected`](~peios/events/peinit/peinit-fd-store-rejected) | standard | `peinit.evman` | peinit refused a file descriptor a service asked it to keep. |
| [`peinit.graph.operation.ended`](~peios/events/peinit/peinit-graph-operation-ended) | verbose | `peinit.evman` | An operation that is a member of a graph execution context reached its terminal outcome as the graph sees it: satisfied, so that what depends on it may proceed, or failed. |
| [`peinit.graph.validation.failed`](~peios/events/peinit/peinit-graph-validation-failed) | standard | `peinit.evman` | The service graph failed validation for the reason in `outcome.reason`. |
| [`peinit.graph.validation.warned`](~peios/events/peinit/peinit-graph-validation-warned) | standard | `peinit.evman` | The service graph passed validation with a warning: nothing was refused, but something will not behave as its author probably expects. |
| [`peinit.internal-error.contained`](~peios/events/peinit/peinit-internal-error-contained) | standard | `peinit.evman` | peinit could not carry out a step on a service's behalf, and contained the fault to that service. |
| [`peinit.job.created`](~peios/events/peinit/peinit-job-created) | verbose | `peinit.evman` | A job exists: peinit has decided to run a process and recorded it, before the process exists. |
| [`peinit.job.ended`](~peios/events/peinit/peinit-job-ended) | standard | `peinit.evman` | A job is over: its process exited or was killed, or the job ended without its process ever starting. |
| [`peinit.job.output.dropped`](~peios/events/peinit/peinit-job-output-dropped) | standard | `peinit.evman` | A submitted job's submitter stopped draining its output, and peinit began dropping the submitter's copy of the job's lines. |
| [`peinit.job.started`](~peios/events/peinit/peinit-job-started) | standard | `peinit.evman` | A job's process exists and has been executed: the moment a process is running as `object.job.token.sid` on peinit's behalf. |
| [`peinit.job.status.reported`](~peios/events/peinit/peinit-job-status-reported) | verbose | `peinit.evman` | A submitted job reported `STATUS=` or `PROGRESS=` on the notification channel, and this is what peinit retained after it. |
| [`peinit.notify.errno.reported`](~peios/events/peinit/peinit-notify-errno-reported) | standard | `peinit.evman` | A service's job sent `ERRNO=`: its own claim about an error, which peinit neither acts on nor retains. |
| [`peinit.notify.exit-status.reported`](~peios/events/peinit/peinit-notify-exit-status-reported) | standard | `peinit.evman` | A service's job sent `EXIT_STATUS=`, informationally; it is not the exit of any process. |
| [`peinit.notify.progress.reported`](~peios/events/peinit/peinit-notify-progress-reported) | verbose | `peinit.evman` | A service's job sent `PROGRESS=` or `PROGRESS_UNIT=`, and this is the progress peinit retained after it. |
| [`peinit.notify.rejected`](~peios/events/peinit/peinit-notify-rejected) | standard | `peinit.evman` | peinit refused a datagram on the notification channel and applied none of it: the sender could not be authenticated, the message did not parse, or it made no sense for the job's state. |
| [`peinit.notify.status.reported`](~peios/events/peinit/peinit-notify-status-reported) | verbose | `peinit.evman` | A service's job sent `STATUS=` on the notification channel. |
| [`peinit.notify.stopping.reported`](~peios/events/peinit/peinit-notify-stopping-reported) | standard | `peinit.evman` | A service's job sent `STOPPING=1`, so peinit will not send it SIGTERM. |
| [`peinit.on-failure.suppressed`](~peios/events/peinit/peinit-on-failure-suppressed) | standard | `peinit.evman` | peinit declined to start an OnFailure handler, because starting it would have looped or gone too deep, so the failure it was meant to handle went unhandled. |
| [`peinit.operation.ended`](~peios/events/peinit/peinit-operation-ended) | standard | `peinit.evman` | An operation reached a terminal state other than `merged`: it completed, failed, was cancelled while still pending, or was aborted while running. |
| [`peinit.operation.merged`](~peios/events/peinit/peinit-operation-merged) | verbose | `peinit.evman` | An operation was absorbed into another before it ran, and has no outcome of its own: follow `object.operation.merged-into.guid` to the operation whose `peinit.operation.ended` decides it. |
| [`peinit.operation.requested`](~peios/events/peinit/peinit-operation-requested) | standard | `peinit.evman` | An operation on a service — a start, stop, restart, reload or reset — was created. |
| [`peinit.operation.started`](~peios/events/peinit/peinit-operation-started) | verbose | `peinit.evman` | An operation left the queue and began to run. |
| [`peinit.recovery.entered`](~peios/events/peinit/peinit-recovery-entered) | essential | `peinit.evman` | peinit dropped the machine to a recovery shell, for the reason in `outcome.reason`. |
| [`peinit.service.abandoned`](~peios/events/peinit/peinit-service-abandoned) | standard | `peinit.evman` | A service's processes survived SIGKILL and its post-kill timeout, so peinit gave up on them and moved the service to `abandoned`: its cgroup is still populated, unkillably. |
| [`peinit.service.reload.timed-out`](~peios/events/peinit/peinit-service-reload-timed-out) | standard | `peinit.evman` | A service announced `RELOADING=1` and never confirmed the reload by its deadline: it wedged mid-reload, or lost its handler. |

## Package Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`peipkg.action.authorised`](~peios/events/peipkg/peipkg-action-authorised) | essential | `peipkg.evman` | The record that the operator was asked to authorise an elevated action specifically, apart from the routine proceed prompt, and what they answered. |
| [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed) | standard | `peipkg.evman` | The record that peipkg granted a role to a package or revoked it, or tried to and failed. |
| [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed) | essential | `peipkg.evman` | The record that peipkg installed a package, or tried to and failed. |
| [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled) | essential | `peipkg.evman` | The record that peipkg removed a package, or tried to and failed. |
| [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded) | essential | `peipkg.evman` | The record that peipkg moved an installed package to another version, or tried to and failed. |
| [`peipkg.repository.added`](~peios/events/peipkg/peipkg-repository-added) | essential | `peipkg.evman` | The record that peipkg added a repository and established trust in it, or tried to and failed. |
| [`peipkg.repository.reconfigured`](~peios/events/peipkg/peipkg-repository-reconfigured) | essential | `peipkg.evman` | The record that a repository add changed one of an existing repository's trust-relevant settings. |
| [`peipkg.repository.refreshed`](~peios/events/peipkg/peipkg-repository-refreshed) | standard | `peipkg.evman` | The record that peipkg refreshed the metadata of its configured repositories. |
| [`peipkg.repository.removed`](~peios/events/peipkg/peipkg-repository-removed) | essential | `peipkg.evman` | The record that peipkg removed a repository from its configuration and database, or tried to and failed. |
| [`peipkg.transaction.recovered`](~peios/events/peipkg/peipkg-transaction-recovered) | standard | `peipkg.evman` | The record that `peipkg recover` reconciled interrupted transactions, rolling back each one it found pending, or failed to. |

## Event Store Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`eventd.config.changed`](~peios/events/eventd/eventd-config-changed) | essential | `eventd.evman` | The record that eventd applied a change to one of its configuration values at runtime. |
| [`eventd.daemon.started`](~peios/events/eventd/eventd-daemon-started) | essential | `eventd.evman` | The record that eventd started, attached to KMES and decided where to resume reading each CPU's ring. |
| [`eventd.daemon.stopped`](~peios/events/eventd/eventd-daemon-stopped) | essential | `eventd.evman` | The record that eventd shut down gracefully, written after it stopped reading the rings and committed everything it had read. |
| [`eventd.events.lost`](~peios/events/eventd/eventd-events-lost) | essential | `eventd.evman` | The record that eventd found events missing from a CPU's ring: sequence numbers it never read and never stored. |
| [`eventd.store.quarantined`](~peios/events/eventd/eventd-store-quarantined) | essential | `eventd.evman` | The record that eventd found one of its stores corrupt, moved it aside and started a new one in its place. |

## Authentication Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`authd.logon.attempted`](~peios/events/authd/authd-logon-attempted) | essential | `authd.evman` | The record that something asked authd to sign a principal in, and whether it did. |
| [`authd.service.attested`](~peios/events/authd/authd-service-attested) | standard | `authd.evman` | The record that the service manager asked authd for a service's token, with no credential behind it, and whether authd minted one. |
| [`authd.session.ended`](~peios/events/authd/authd-session-ended) | essential | `authd.evman` | The record that authd ended a logon session at someone's request, by ending every process whose primary token belongs to it (PGSS Logon <span>§</span>2.22). |

## Local Principal Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`lpsd.account.created`](~peios/events/lpsd/lpsd-account-created) | essential | `lpsd.evman` | The record that an administrator created a local account with `lps`, or tried to. |
| [`lpsd.account.deleted`](~peios/events/lpsd/lpsd-account-deleted) | essential | `lpsd.evman` | The record that an administrator deleted a local account with `lps`, or tried to. |
| [`lpsd.account.modified`](~peios/events/lpsd/lpsd-account-modified) | essential | `lpsd.evman` | The record that an account was changed: by an administrator with `lps`, or by the principal themselves where the self socket allows it. |
| [`lpsd.credential.changed`](~peios/events/lpsd/lpsd-credential-changed) | essential | `lpsd.evman` | The record that a principal changed their own password, or added or removed one of their own SSH keys, through authd (PSPU <span>§</span>2.21, <span>§</span>2.23), or tried to and was refused. |
| [`lpsd.credential.verified`](~peios/events/lpsd/lpsd-credential-verified) | standard | `lpsd.evman` | The record that lpsd checked a credential for a logon authd relayed to it, and what it found. |
| [`lpsd.group.created`](~peios/events/lpsd/lpsd-group-created) | essential | `lpsd.evman` | The record that an administrator created a local group with `lps`, or tried to. |
| [`lpsd.group.deleted`](~peios/events/lpsd/lpsd-group-deleted) | essential | `lpsd.evman` | The record that an administrator deleted a local group with `lps`, or tried to. |
| [`lpsd.group.member.added`](~peios/events/lpsd/lpsd-group-member-added) | essential | `lpsd.evman` | The record that an administrator added an account to a group with `lps`, or tried to. |
| [`lpsd.group.member.removed`](~peios/events/lpsd/lpsd-group-member-removed) | essential | `lpsd.evman` | The record that an administrator removed an account from a group with `lps`, or tried to. |

## Time Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`timed.clock.stepped`](~peios/events/timed/timed-clock-stepped) | essential | `timed.evman` | timed moved the system clock at once by an arbitrary amount, rather than adjusting its rate. |

## Network Configuration Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`netd.hostname.changed`](~peios/events/netd/netd-hostname-changed) | essential | `netd.evman` | netd changed the machine's hostname. |

## Trust Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`trustd.root.added`](~peios/events/trustd/trustd-root-added) | standard | `trustd.evman` | A root certificate authority entered the set this machine trusts. |
| [`trustd.root.distrusted`](~peios/events/trustd/trustd-root-distrusted) | standard | `trustd.evman` | A distrust took a root certificate authority out of the set this machine trusts. |
| [`trustd.root.removed`](~peios/events/trustd/trustd-root-removed) | standard | `trustd.evman` | A root certificate authority left the set this machine trusts, and no distrust names it: its addition was withdrawn, or a bundle upgrade dropped it. |

## Not in the catalogue

The registry's [watch records](~peios/events/registry-watch-records/watch-records) are not events, so no fragment defines them and this table does not list them.

*Generated from the evman catalogue by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
