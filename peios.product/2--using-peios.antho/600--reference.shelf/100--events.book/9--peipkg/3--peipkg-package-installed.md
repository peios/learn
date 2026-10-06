---
title: "peipkg.package.installed"
description: "The record that peipkg installed a package, or tried to and failed."
---

- **Event type:** `peipkg.package.installed`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every installation is recorded
- **Cardinality:** once per package a transaction installs; once per named package on a rejected request

The record that peipkg installed a package, or tried to and failed. A
transaction writes one record for each package its plan installs, whichever
command ran it: an `upgrade` that pulls in a new dependency writes this
event for the dependency, and undoing an uninstall writes it for the
package restored. A request refused before any transaction opened writes
one failed record for each package it named.

Essential because a package installation changes what the system runs, and
it is rare. Replaces `peipkg.install`, and the install half of
`peipkg.transaction-failed`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The operator: the user SID of the token peipkg ran under. This is peipkg's own word; the kernel-stamped `emitter.token.guid` is the identity it cannot forge. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | The peipkg transaction, for every record of one transaction. Absent when the request was refused before a transaction opened, or when a cross-root transaction failed while preparing its roots. In a cross-root transaction, the transaction of the root this package is installed in. |
| [`object.package.name`](~peios/events/field-index/fields-object#object.package.name) | `str` | optional | Absent only on a refused request that named no package. |
| [`object.package.version`](~peios/events/field-index/fields-object#object.package.version) | `str` | optional | The version installed. Absent on a refused request that named no version. |
| [`object.package.architecture`](~peios/events/field-index/fields-object#object.package.architecture) | `str` | optional | The architecture of the package an event is about: an identifier of PSPU <span>§</span>5.8, such as `x86_64`, `aarch64` or `noarch`. |
| [`source.repository.name`](~peios/events/field-index/fields-source#source.repository.name) | `str` | optional | Absent for an install from a local file. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | peipkg's stable error code for the failure, the one its driven mode reports. Whether anything was rolled back follows from `transaction.id`: a failure with one was rolled back, a failure without one was refused before it began.<br><br>Values here (open set): `stale` · `busy` · `denied` · `unowned` · `alternate-upgrade` · `unresolvable` · `untrusted` · `failed`. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | The error as peipkg reported it to the operator. Absent on success. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
