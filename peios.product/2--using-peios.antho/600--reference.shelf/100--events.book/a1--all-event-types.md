---
title: "All Event Types"
description: "Every event type the evman catalogue defines, in one table: its tier, its defining fragment and its one-line summary, generated from the fragments."
---

Every event type in the evman catalogue, generated from the fragments by `pkm/tools/gen-events-book.py`: 20 event types and 581 fields, from `kacs.evman`, `kernel.evman`, `kmes.evman`, `lcs.evman`, `ntfe.evman`, `stratafs.evman`, `peinit.evman`, `peipkg.evman`, `eventd.evman`.

The tier sets whether an event type is recorded by default (PGSS §6.8). Each type links to its page; each page's fields link to the field index.

## Access and Identity Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) | essential | `kacs.evman` | The record that an access check completed, and what it decided. |
| [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) | standard | `kacs.evman` | The record of what was done with a handle after it was opened. |
| [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) | essential | `kacs.evman` | The record that a privilege contributed access to a check, and whether that contribution survived. |
| [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) | standard | `kacs.evman` | The record that a central access policy rule's SACL could not be parsed or evaluated, so the audit it asked for was skipped. |
| [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) | standard | `kacs.evman` | The record that a staged central access policy would have decided an access differently from the policy in force. |
| [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected) | standard | `kacs.evman` | The record that KACS read an object's stored security descriptor, found it corrupt, and refused to use it. |
| [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed) | standard | `kacs.evman` | The record that a logon session ended because its last token went away. |
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
| [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened) | essential | `lcs.evman` | The record that a registry key was opened and what access the open received. |
| [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended) | essential | `lcs.evman` | The record that a registry subtree restore finished, successfully or otherwise. |
| [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started) | essential | `lcs.evman` | The record that a registry subtree restore began, emitted **before any state is modified**. |
| [`lcs.config.value.rejected`](~peios/events/lcs/lcs-config-value-rejected) | standard | `lcs.evman` | The record that LCS read one of its own configuration values, rejected it, and carried on with what it had. |
| [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected) | essential | `lcs.evman` | The record that LCS rejected data a registry source sent it. |

## Event Stream Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`kmes.buffer.swap.failed`](~peios/events/kmes/kmes-buffer-swap-failed) | standard | `kmes.evman` | The record that KMES could not resize its per-CPU ring buffers and kept the capacity it had. |
| [`kmes.config.value.rejected`](~peios/events/kmes/kmes-config-value-rejected) | standard | `kmes.evman` | The record that KMES read a configuration value, rejected it, and carried on with what it had. |

## Network Policy Events

| Event type | Tier | Fragment | Summary |
|---|---|---|---|
| [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported) | standard | `ntfe.evman` | The record of a traffic policy decision that a rule explicitly asked to be reported. |

## Not yet in the catalogue

peinit, peipkg and eventd define their fields in the catalogue but do not yet write catalogue events. What they emit today is in [Service Events](~peios/events/service-events/job-events), [Package Events](~peios/events/package-events/the-event-set) and [Event Daemon Events](~peios/events/event-daemon-events/synthetic-events). The registry's [watch records](~peios/events/registry-watch-records/watch-records) are not events at all.

*Generated from the evman catalogue by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
