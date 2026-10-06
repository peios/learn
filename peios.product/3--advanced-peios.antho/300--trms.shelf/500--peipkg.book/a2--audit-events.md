---
title: Audit Events
description: Every audit event peipkg emits — the types, their tiers and payload fields, where events do not appear, and what emission depends on.
---

Every event described here is emitted into the kernel event subsystem
(§13.3). Each type and field is defined in peipkg's evman fragment,
installed as `/usr/share/evman/peipkg.evman`, which is the authoritative
description; this appendix summarises it.

These types also appear in the
[Peios Events Index](~peios/events/all-event-types), a page per type, alongside
every other event the system emits.

## Types

| Type | Tier | Written for |
|---|---|---|
| `peipkg.package.installed` | essential | Each package a transaction installs, or a request to install one that failed |
| `peipkg.package.upgraded` | essential | Each package a transaction moves to another version — upgrade, downgrade or undo — or a request to that failed |
| `peipkg.package.uninstalled` | essential | Each package a transaction removes, or a request to remove one that failed |
| `peipkg.repository.added` | essential | A repository add and its trust ceremony, successful or failed |
| `peipkg.repository.removed` | essential | A repository removal, successful or failed |
| `peipkg.repository.reconfigured` | essential | Each trust-relevant setting a repository add changed |
| `peipkg.repository.refreshed` | standard | A refresh, successful or partly failed |
| `peipkg.claim.changed` | standard | A claim grant or revoke, successful or failed |
| `peipkg.transaction.recovered` | standard | Every run of `peipkg recover`, successful or failed |
| `peipkg.action.authorised` | essential | An elevated action put to the operator, authorised or declined |

An essential type is always written. A standard type is written unless the
system's emission policy switches it off.

## Payload fields

Every record carries `subject.token.sid`, the user SID of the token peipkg
ran under. A field that does not apply is absent.

| Field | Carried by | Content |
|---|---|---|
| `transaction.id` | package, claim | The transaction; in a cross-root transaction, the transaction of the package's own root. Absent when none opened |
| `object.package.name` | package, authorised | The package |
| `object.package.version` | package | The version installed, moved to, or removed |
| `object.package.version-previous` | upgraded | The version moved from |
| `object.package.architecture` | installed, upgraded | The package's architecture |
| `source.repository.name` | installed, upgraded | The repository the package came from; absent for a local file |
| `object.repository.name` | repository, authorised | The repository |
| `object.repository.url` | added | Its base URL |
| `config.name` | reconfigured | The setting, as the repository file names it |
| `config.text`, `config.text-previous` | reconfigured | `signature_policy`, new and old |
| `config.value`, `config.value-previous` | reconfigured | Any other setting, new and old: days or an index version; 1 or 0 for `allow_insecure_transport`; the anchor count for `trust_anchors` |
| `object.claim.role`, `object.claim.holder` | claim | The role, and its new holder; no holder on a revoke |
| `operation.succeeded-count`, `operation.failed-count` | refreshed | Repositories refreshed and failed |
| `operation.succeeded-count` | recovered | Interrupted transactions rolled back |
| `operation.name` | authorised | `low-trust-provides`, `foreign-replaces`, `downgrade`, `remove-modified-file`, `stale-trust-state` or `stale-index` |
| `object.file.path` | authorised | The modified file, for `remove-modified-file` |
| `outcome.success` | all but reconfigured | Whether it succeeded; for authorised, whether the operator agreed |
| `outcome.reason` | package, claim, added | On failure, peipkg's error code |
| `outcome.detail` | all but reconfigured and refreshed | On failure, the error text; for authorised, the action as it was put |

A failed package record with a transaction identifier was rolled back; one
without was refused before any transaction opened. A cross-root transaction
that fails while preparing its roots leaves no identifier on its records.

## Where events do not appear

- Automatic recovery at the head of an ordinary operation writes nothing.
- Declining the routine proceed prompt writes nothing.
- A repository add refused before it names a base URL writes nothing.
- A refresh that fails before reaching any repository writes nothing.
- A stale repository refused because `--allow-stale` was not given writes
  no authorisation record; only proceeding with one does.
- Enabling insecure transport, and installing unsigned content under an
  `optional` policy, write no authorisation record.
- `peipkg-compose` writes nothing at all.

## What emission depends on

An audit privilege on the caller's token. Without it, emission fails,
peipkg warns, and the operation proceeds unaudited, essential types
included.

On a kernel with no emit call, emission is a silent successful no-op.
