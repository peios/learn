---
title: The Event Set
description: The eleven event types peipkg emits, their payload fields, and the privilege emission depends on.
---

peipkg emits eleven event types into the kernel event subsystem. The
caller's identity is stamped into the envelope by the kernel (§1.2) and
is not part of the payload.

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

`peipkg.config-change` is specified and **not emitted**. A trust-policy
or transport-flag change today produces no event at all.

## Payload fields

| Field | Content |
|---|---|
| `txn_id` | The transaction identifier. |
| `outcome` | `success`, `rejection`, or `rollback`. |
| `repo` | The repository, for repository operations. |
| `detail` | The rejection reason, the operation count, or the authorised action. |
| `timestamp` | RFC 3339, UTC. |
| `packages` | Name, version and architecture per package. |

Note `timestamp` here is an **RFC 3339 string**, not the uint used
elsewhere in this book (§1.3). peipkg carries its own.

## Emission depends on a privilege

An audit privilege on the caller's token. Without it, emission fails,
peipkg warns, and **the operation proceeds unaudited**. The absence of
an event does not mean the operation did not happen.

On a kernel with no emit call, emission is a silent successful no-op.
