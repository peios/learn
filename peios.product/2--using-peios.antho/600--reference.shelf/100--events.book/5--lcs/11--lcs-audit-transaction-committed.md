---
title: "lcs.audit.transaction.committed"
description: "The record of how a registry transaction ended, written for a transaction that staged at least one write some other record covers."
---

- **Event type:** `lcs.audit.transaction.committed`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** the transaction staged at least one recorded write
- **Cardinality:** once per transaction that staged a recorded write

The record of how a registry transaction ended, written for a transaction
that staged at least one write some other record covers. Transacted
writes are recorded when they are staged; this says whether they took
effect, joined to them on `transaction.id`.

It is written once, at the end: when `REG_IOC_COMMIT` leaves the
transaction committed or otherwise finished, when it times out, or when
its fd is closed without a commit. A commit that fails and leaves the
transaction open writes nothing yet.

**A commit that timed out may have taken effect.** The commit was sent
and not answered; `transaction.commit-outstanding` true says so, and the
source may have applied it before the reply was lost.

**The subject depends on how it ended.** On `REG_IOC_COMMIT` it is the
subject who committed, not who staged the writes. A transaction that ended
by timeout or by its fd closing has nobody acting, and names the subject
that staged its first recorded write.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`caller`](~peios/events/groups/group-caller) | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`caller`](~peios/events/groups/group-caller) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`caller`](~peios/events/groups/group-caller) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`caller`](~peios/events/groups/group-caller) | The impersonation level of the effective token. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | required | The transaction the operation belonged to, registry or package. |
| [`transaction.state`](~peios/events/field-index/fields-transaction#transaction.state) | `str.enum` | required | The state it ended in: `committed` on success. |
| [`transaction.commit-outstanding`](~peios/events/field-index/fields-transaction#transaction.commit-outstanding) | `bool` | when `outcome.success == false` | Whether a transaction's commit had been sent to its source and not yet answered. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True only when the transaction committed. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | optional | Present when a `REG_IOC_COMMIT` call failed; absent for a transaction that ended without one. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | `aborted` when its fd was closed without a commit or a layer it wrote was deleted, `timed-out` when it passed its deadline, `source-error` when its source failed or went away.<br><br>Values here (open set): `aborted` · `timed-out` · `source-error`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
