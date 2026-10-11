---
title: "transaction.*"
description: "Every field the evman catalogue defines under transaction: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `transaction`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="transaction.commit-outstanding"></a>`transaction.commit-outstanding`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a transaction's commit had been sent to its source and not yet
answered. When this is true and the transaction then times out or its
source goes down, nobody can say whether the changes were applied: the
source may have committed them before the reply was lost.

**Carried by:**

- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)

## <a id="transaction.id"></a>`transaction.id`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The transaction the operation belonged to, registry or package. A pure
correlation identifier: every record of one transaction carries the same
value, from begin to commit or abort. The registry and the package manager
number their transactions independently, so an identifier is unique only
within one of them; which it belongs to follows from the event type.

**Carried by:**

- [`lcs.audit.key.created`](~peios/events/lcs/lcs-audit-key-created)
- [`lcs.audit.key.deleted`](~peios/events/lcs/lcs-audit-key-deleted)
- [`lcs.audit.key.descriptor.changed`](~peios/events/lcs/lcs-audit-key-descriptor-changed)
- [`lcs.audit.key.hidden`](~peios/events/lcs/lcs-audit-key-hidden)
- [`lcs.audit.key.tombstoned`](~peios/events/lcs/lcs-audit-key-tombstoned)
- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)
- [`lcs.audit.value.deleted`](~peios/events/lcs/lcs-audit-value-deleted)
- [`lcs.audit.value.set`](~peios/events/lcs/lcs-audit-value-set)
- [`peipkg.claim.changed`](~peios/events/peipkg/peipkg-claim-changed)
- [`peipkg.package.installed`](~peios/events/peipkg/peipkg-package-installed)
- [`peipkg.package.uninstalled`](~peios/events/peipkg/peipkg-package-uninstalled)
- [`peipkg.package.upgraded`](~peios/events/peipkg/peipkg-package-upgraded)

## <a id="transaction.position"></a>`transaction.position`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The ordinal of a mutation within its registry transaction, counting from
1 in the order the mutations were made. Correlates one operation with its
place in a commit that applies many.

**Carried by:**

No event carries this field yet.

## <a id="transaction.state"></a>`transaction.state`

- **Type:** `str.enum`
- **Values:** `active-unbound` · `active-bound` · `committed` · `aborted` · `timed-out` · `source-down`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The state of a registry transaction, from the `REG_TXN_*` states. A
transaction is `active-unbound` until its first mutation binds it to a
source and hive, then `active-bound`. The other four are terminal:
`committed`, `aborted`, `timed-out` when it passed its deadline, and
`source-down` when the source holding it went away.

`timed-out` and `source-down` do not by themselves say whether the
transaction's changes landed; see `transaction.commit-outstanding`.

**Carried by:**

- [`lcs.audit.transaction.committed`](~peios/events/lcs/lcs-audit-transaction-committed)

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
