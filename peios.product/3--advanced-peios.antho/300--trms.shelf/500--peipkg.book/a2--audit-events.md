---
title: Audit Events
description: Every audit event peipkg emits — the types, their payload fields, where events do not appear, and what emission depends on.
---

Every event described here is emitted into the kernel event subsystem
(§13.3). The caller's identity is stamped into the event header by the
kernel and is not part of the payload.

These types also appear in the
[Peios Events Index](~peios/package-events/the-event-set), alongside
every other event the system emits.

## Types

| Type | Emitted for | Emitted today |
|---|---|---|
| `peipkg.install` | A successful install | yes |
| `peipkg.upgrade` | A successful upgrade, downgrade, or undo | yes |
| `peipkg.uninstall` | A successful uninstall | yes |
| `peipkg.refresh` | A repository refresh, successful or partially failed | yes |
| `peipkg.transaction-failed` | A rejected or rolled-back transaction | yes |
| `peipkg.recovery` | A recovery resolved through `peipkg recover` | yes |
| `peipkg.authorisation` | An operator authorisation record | yes |
| `peipkg.repo-add` | A repository add | yes |
| `peipkg.repo-remove` | A repository remove | yes |
| `peipkg.claim` | A claim grant or revoke | yes |
| `peipkg.config-change` | A trust-policy or transport-flag change | **no** |

## Payload fields

| Field | Content |
|---|---|
| `txn_id` | The transaction identifier |
| `outcome` | `success`, `rejection`, or `rollback` |
| `repo` | The repository, for repository operations |
| `detail` | The rejection reason, the operation count, or the authorised action |
| `timestamp` | RFC 3339, UTC |
| `packages` | Name, version, architecture, and source repository per package |

The source repository is per package rather than per event, because one
plan can draw from several. An empty value means one of three things,
which the event type tells apart: a removal has no source, a raw
local-file install has no repository, and an orphaned package's origin
is no longer configured.

## Where events do not appear

- A committed cross-root operation's success event carries no
  transaction identifier.
- Automatic recovery at the head of an ordinary operation emits nothing.
- `peipkg recover`'s failure paths emit nothing.
- Declining at a prompt emits nothing.
- Enabling insecure transport, and installing unsigned content under an
  `optional` policy, emit no authorisation record.
- `peipkg-compose` emits nothing at all.

## What emission depends on

An audit privilege on the caller's token. Without it, emission fails,
peipkg warns, and the operation proceeds unaudited.

On a kernel with no emit call, emission is a silent successful no-op.
