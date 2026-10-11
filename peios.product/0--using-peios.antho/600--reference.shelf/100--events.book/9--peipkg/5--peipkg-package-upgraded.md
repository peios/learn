---
title: "peipkg.package.upgraded"
description: "The record that peipkg moved an installed package to another version, or tried to and failed."
---

- **Event type:** `peipkg.package.upgraded`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every upgrade, downgrade and undo is recorded
- **Cardinality:** once per package a transaction moves to another version; once per named package on a rejected request

The record that peipkg moved an installed package to another version, or
tried to and failed. A downgrade and an undo are recorded here too:
comparing `object.package.version` with `object.package.version-previous`
by PSPU <span>§</span>5.6 tells which way the package moved. A refused downgrade or undo
is recorded here as well, with the version it asked for.

Replaces `peipkg.upgrade`, and the upgrade half of
`peipkg.transaction-failed`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | Absent when the request was refused before a transaction opened, or when a cross-root transaction failed while preparing its roots. |
| [`object.package.name`](~peios/events/field-index/fields-object#object.package.name) | `str` | optional | Absent only on a refused request that named no package, such as an upgrade of everything. |
| [`object.package.version`](~peios/events/field-index/fields-object#object.package.version) | `str` | optional | The version the package moved to. |
| [`object.package.version-previous`](~peios/events/field-index/fields-object#object.package.version-previous) | `str` | optional | The version it moved from. Absent on a refused request. |
| [`object.package.architecture`](~peios/events/field-index/fields-object#object.package.architecture) | `str` | optional | The architecture of the package an event is about: an identifier of PSPU <span>§</span>5.8, such as `x86_64`, `aarch64` or `noarch`. |
| [`source.repository.name`](~peios/events/field-index/fields-source#source.repository.name) | `str` | optional | Absent for an upgrade from a local file. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `stale` · `busy` · `denied` · `unowned` · `alternate-upgrade` · `unresolvable` · `untrusted` · `failed`. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | Free text about the outcome, for a person to read. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
