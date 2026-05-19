---
title: Transactions
---

A transaction is the atomic unit of package operations.
All install, upgrade, and uninstall procedures (§7.1, §7.2,
§7.3) execute within a transaction, even when the
transaction contains a single operation.

This section defines the transaction model and its
properties.

## Atomicity

A transaction is *atomic*: either all of its operations
succeed and become visible to consumers of the system, or
none of them visibly take effect.

This property MUST hold under both:

- Logical failure (a step fails, an error is reported, a
  rollback is requested).
- System failure (power loss, kernel panic, hardware
  fault) at any point during the transaction.

A transaction in progress is *uncommitted*. An uncommitted
transaction is not visible to other consumers of the
system: the package database does not yet show its
operations as applied; files staged for replacement have
not yet replaced their targets; side effects have not yet
been invoked.

A transaction that completes its commit step (§7.4.5) is
*committed*. A committed transaction's operations are
visible to all subsequent operations.

## Transaction scope

A transaction MAY contain any combination of install,
upgrade, and uninstall operations on different packages.
Operations within a single transaction MUST be ordered
such that, at commit time, no operation depends on a
package whose install has not been committed first.

A transaction MUST NOT contain two operations that affect
the same package (e.g., install and uninstall the same
package within the same transaction). Use upgrade for
version transitions; use removal-then-install (in two
separate transactions) for hard reinstalls.

## Verification before extraction

For a transaction containing multiple install or upgrade
operations, the package manager MUST complete signature
verification (§5.3.2) and index-hash verification
(§3.5.3 step 2) for *every* package in the transaction
before extracting (§7.1.2.3) any package's payload.

A package whose verification fails MUST cause the entire
transaction to be aborted before any payload extraction
begins.

> [!INFORMATIVE]
> This rule prevents a class of multi-package attack
> where package A is verified, extracted, and its
> contents influence the verification or extraction of
> package B (e.g., A installs a tool that B's
> extraction process invokes; A creates a directory
> whose SD affects where B's files land). Verifying all
> packages first means the transaction operates on a
> known-good set of payloads.

## Single-writer concurrency

At most one transaction MAY be in progress at any time on
a given system.

The package manager MUST acquire an exclusive lock before
beginning a transaction. Other concurrent invocations of
the package manager MUST detect the lock and either:

- Wait for the in-progress transaction to complete.
- Fail with an explicit "transaction in progress" error.

The lock mechanism is implementation-defined but MUST
provide:

- Mutual exclusion across processes on the same system.
- Detection of stale locks (held by terminated processes).
- A user-visible error message when blocking.

> [!INFORMATIVE]
> A common implementation is a lock file at a known path
> (e.g., `/var/lib/peipkg/lock`) using `flock(2)` or
> equivalent. Stale-lock detection inspects whether the
> holding process is still alive.

Stale-lock detection MUST be conservative: the package
manager MUST NOT declare a lock stale based on a
timeout alone. Stale-detection MUST verify that the
holder is provably gone (e.g., `kill(pid, 0) == ESRCH`
plus a PID-reuse safeguard such as comparing the
process start time recorded in the lock against the
current process's start time).

> [!INFORMATIVE]
> A timeout-only stale check breaks single-writer
> atomicity: a long-running but live transaction (e.g.,
> a 50-package install on a slow disk) could be
> mistakenly declared dead by another invocation, with
> both transactions then proceeding concurrently. The
> conservative check trades responsiveness for
> correctness, which is the right trade for a
> security-critical lock.

> [!INFORMATIVE]
> Read-only queries against the committed package database
> (`peipkg query installed`, dependency resolution against
> cached indexes, etc.) do NOT require the transaction
> lock. Such queries observe only committed state per
> §7.4.8 and run concurrently with an in-progress
> transaction.

## Commit procedure

The commit procedure transitions a transaction from
uncommitted to committed. Atomicity rests on a single
fact: the package database is a transactional store
(SQLite in WAL mode, or equivalent — §7.4.8), and **the
package database's own commit is the transaction's
durability boundary.** No separate commit protocol is
layered on top of it.

1. **Record intent.** Before any file is moved, write the
   transaction's intent to the journal — the set of file
   operations, and for each the staged-file path and the
   path its displaced original will be backed up to (the
   *backup map*). The journal is part of the package
   database (§7.4.5.1); recording intent is an ordinary
   database write.
2. **Apply file operations.** For each operation, rename
   any displaced original aside as a backup (§7.5.1.3)
   and rename the staged file into place (§7.2 step 4,
   §7.3 step 3). Throughout this phase every change is
   individually reversible from the backup map.
3. **Commit.** In a single package-database transaction,
   write the new installed-package state and mark the
   journal's pending transaction `committed`. This
   database commit is the durability boundary: it is
   atomic, so the transaction is either fully committed
   or not committed at all.
4. **Invoke deduplicated side effects** (§7.4.6). Side
   effects run *after* the durability boundary; a
   side-effect failure therefore does not roll the
   transaction back — side effects are idempotent (§4.3),
   the transaction is already committed, and a failed
   side effect is reported and corrected by re-invocation.
5. **Clean up.** Discard staged files; backups become
   eligible for the retention window (§7.5.1.3).

A crash *before* step 3's database commit leaves the
journal's transaction `pending`; recovery rolls it back
(§7.4.7). A crash *after* it leaves the transaction
`committed`; recovery has only clean-up to finish. The
transaction is never found partly committed, so recovery
never completes a half-finished commit.

### The journal

The transaction journal is **part of the package
database**: the pending transaction is recorded as rows
in the package-database store, not as a separate file
with a separate format. Recording intent (§7.4.5 step 1)
and committing (step 3) are therefore ordinary database
writes, and the journal inherits the database's
transactional guarantees (§7.4.8).

The package database — and therefore the journal — is
stored under a security descriptor that grants write
access only to the install-authority tier (the
principals permitted to install packages on the system).
That security descriptor is the journal's integrity
protection: a principal outside the tier cannot forge a
journal entry, and a principal inside the tier already
holds installation authority, so a within-tier write is
not an escalation.

The staging area is stored under the same security
descriptor.

> [!INFORMATIVE]
> Earlier drafts specified an HMAC over each commit
> record, keyed to a dedicated package-manager principal.
> Peios's package manager runs as the calling operator
> and holds no principal of its own (§7.6), so there is
> no principal-bound key to HMAC with; the security
> descriptor on the package database is the protection
> instead. A future hardening — once Peios's
> elevated-executable mechanism exists — can narrow that
> security descriptor so the journal is writable only
> *through* the package-manager executable rather than
> by the install-authority tier at large. That is an
> optional tightening, not a v0.22 requirement.

## Side-effect deduplication

A transaction MAY contain multiple operations that each
declare the same side effect (e.g., installing several
packages that all declare `ldconfig`). Side effects MUST
be deduplicated and invoked once per transaction, after
all file-level operations are complete.

Side effects are invoked in implementation-defined order.
The fixed enumerated set of recognised side effects (§4.3)
is designed such that order between distinct side effects
is not significant. An implementation MAY invoke distinct
side effects concurrently.

Future versions of this specification that add new
side-effect identifiers MUST explicitly state whether
the new effect is order-independent with respect to the
existing set. Order-dependent side effects (if ever
added) MUST be specified with a normative ordering
relative to all other recognised side effects.

## Crash recovery

On startup, before permitting any new transaction, the
package manager MUST check the journal for a pending
transaction:

1. **No pending transaction** — the package database
   shows no transaction in the `pending` state: no
   recovery is needed.
2. **A pending transaction exists**: **roll it back**.
   Restore every displaced original from the backup map,
   discard the transaction's staged files, and clear the
   pending transaction from the journal.

There is no roll-*forward*. Because the database commit
(§7.4.5 step 3) is the single durability boundary and is
itself atomic, a recovered transaction is only ever in
one of two states: committed (the database records it
committed — nothing to recover) or pending (roll back). A
transaction is never found partly committed, so recovery
never has to complete a half-finished commit.

Recovery is itself crash-safe: every action it takes is a
rename from the backup map, and re-running it after an
interruption produces the same result.

> [!INFORMATIVE]
> Roll-back-only recovery is possible because the package
> database is a transactional store. A design that
> applies file changes *after* a separate commit-intent
> record needs roll-forward to finish what that record
> promised; here the database commit and the "transaction
> is done" fact are the same atomic event, so there is
> nothing left to finish.

## Visibility

The package database state visible to queries (`peipkg
query installed`, etc.) MUST reflect only committed
transactions.

The package database MUST provide snapshot-isolation
reads: a query that begins reading the database at time
T MUST see a consistent snapshot of committed state as
of T, regardless of write transactions that commit
during the query. A flat-file database read with naive
`read(2)` does NOT satisfy this requirement; SQLite in
WAL mode, or an equivalent transactional store with
snapshot isolation, does.

In-progress transaction state SHOULD NOT be visible to
non-package-manager processes. Staged files MUST NOT
appear at their final install paths until commit.

The package manager MAY internally inspect uncommitted
state for purposes of the transaction itself (e.g.,
verifying staged files); this is not a visibility leak.
