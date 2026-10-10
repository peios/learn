---
title: "peipkg.package.uninstalled"
description: "The record that peipkg removed a package, or tried to and failed."
---

- **Event type:** `peipkg.package.uninstalled`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every uninstallation is recorded
- **Cardinality:** once per package a transaction removes; once per named package on a rejected request

The record that peipkg removed a package, or tried to and failed. A
transaction writes one record for each package its plan removes, including
a package removed to resolve a conflict during an install, and a package
removed by undoing its install.

Replaces `peipkg.uninstall`, and the uninstall half of
`peipkg.transaction-failed`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | Absent when the request was refused before a transaction opened. |
| [`object.package.name`](~peios/events/field-index/fields-object#object.package.name) | `str` | required | The name of the package the event is about. |
| [`object.package.version`](~peios/events/field-index/fields-object#object.package.version) | `str` | optional | The version removed. Absent on a refused request. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `stale` · `busy` · `denied` · `unowned` · `alternate-upgrade` · `unresolvable` · `untrusted` · `failed`. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | Free text about the outcome, for a person to read. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
