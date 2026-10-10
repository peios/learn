---
title: Transactions
type: how-to
description: Apply related registry changes atomically in one hive, understand per-file batch limits, and check state before retrying a timed-out commit.
related:
  - peios/registry-layers/what-layers-are-for
  - peios/registry-layers/layers
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-administration/lcs-and-sources
  - peios/registry-concepts/overview
---

Use a transaction when several registry changes must become visible
together. `reg apply` and Registry Editor's **Import…** provide an
operator-facing way to apply a registry document as one batch.

<a id="transactions-in-one-sentence"></a>
<span id="transactions--transactions-in-one-sentence"></span>
<span id="registry-advanced-transactions--transactions-in-one-sentence"></span>
<span id="using-peios-registry-advanced-transactions--transactions-in-one-sentence"></span>
<a id="all-or-nothing"></a>
<span id="transactions--all-or-nothing"></span>
<span id="registry-advanced-transactions--all-or-nothing"></span>
<span id="using-peios-registry-advanced-transactions--all-or-nothing"></span>
## Apply one reviewed document

Prepare or review a JSON registry document, then apply it with:

```sh
reg apply reviewed.json
```

`reviewed.json` is your reviewed file. All its operations must target one
hive; cross-hive batches are rejected even if both hives use the same
source. JSON is supported input; text-format batch input is not implemented.

`reg export --json KEY FILE` creates a reviewable starting point containing
keys and effective values. It does not export key descriptors. A manually
prepared document can include descriptor changes, which must be reviewed
as security changes and need the relevant rights. See
[`reg apply`](~peios/registry-tools/reg#reg-apply-file) for its schema and
version caveat for descriptor support.

A successful transaction publishes its changes together. Other readers do
not see intermediate writes; reads inside a bound transaction see their
own pending writes. This is registry atomicity, not a guarantee that all
consuming services will apply the new configuration simultaneously.

## Limits worth knowing

- **One hive per batch.** Cross-hive atomicity is not available.
- **Directory imports are separate batches.** `reg apply --dir DIR` applies
  each file in its own transaction; the directory is not one atomic unit.
- **No nesting or savepoints.** Keep each document's recovery scope clear.
- **Bounded time and size.** A transaction can time out or exceed resource
  limits. `reg apply` errors need investigation, not an assumption that
  splitting the file preserves its consistency requirements.
- **Source support is required.** A source can reject the needed transaction
  mode; the default `loregd` supports transactions.

<a id="the-canonical-use-installing-a-role"></a>
<span id="transactions--the-canonical-use-installing-a-role"></span>
<span id="registry-advanced-transactions--the-canonical-use-installing-a-role"></span>
<span id="using-peios-registry-advanced-transactions--the-canonical-use-installing-a-role"></span>
<a id="transactions-and-layers"></a>
<span id="transactions--transactions-and-layers"></span>
<span id="registry-advanced-transactions--transactions-and-layers"></span>
<span id="using-peios-registry-advanced-transactions--transactions-and-layers"></span>
## Atomic changes and removable changes are different

A role can use a transaction to apply related registry entries together
and a layer to keep those entries removable later. A transaction does
not select the winning layer or create a history of previous states.
Layer removal also does not undo a key's descriptor changes.

Review [layer recovery](~peios/registry-layers/what-layers-are-for) separately
from whether the original write was atomic.

## Avoid overwriting another writer

Transactions are not value-level conflict detection. If your change
depends on a value remaining unchanged since you read it, use the
conditional-write mechanism rather than assuming the transaction protects
that read.

`reg set --expected-seq N` checks the destination layer's own entry. A
mismatch returns exit status `6` without the write. `reg get -L` shows only
the effective winner, so its sequence is suitable only when that winner
is in your intended destination layer. It does not expose a shadowed
layer's sequence.

## If a commit times out

> [!WARNING]
> A timeout after commit dispatch means the operation may or may not have
> committed. Read the affected state and inspect consumer events before
> retrying. A timed-out transaction status is not proof of rollback.

A source failure returned during commit can also follow a successful
storage commit. Check current state before resubmitting a batch after
such an error.

A late successful response can publish the committed change and notify
watchers even after the caller was told it timed out. Closing an
uncommitted transaction normally aborts it, as does process exit, but
that is not a way to undo an already-dispatched successful commit.

The [LCS commit and failure reference](~peios/lcs/transactions/commit-and-failure)
describes these outcomes. After a successful batch, use the same
[consumer verification](~peios/registry-concepts/configuration-and-meaning)
as for a single write.

## Where to go next

- [`reg` batch formats and exit statuses](~peios/registry-tools/reg)
- [Restore a saved subtree](~peios/registry-administration/backup-and-restore)
- [LCS transaction scope and lifetime](~peios/lcs/transactions/scope-and-lifetime)
- [Isolation and conditional writes](~peios/lcs/transactions/isolation-and-the-mutation-log)
