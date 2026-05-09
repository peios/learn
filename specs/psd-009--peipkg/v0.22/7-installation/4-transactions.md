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
uncommitted to committed. It is the operation that
determines all-or-nothing atomicity.

1. **Verify integrity of staged state**: every staged
   file is in place and verified; the new database state
   has been written to a transaction journal.
2. **Persist commit intent**: write a commit record to
   the transaction journal indicating "this transaction
   is being committed". This record is the durable
   atomicity boundary; before it is persisted, the
   transaction is rolled back on recovery (§7.5);
   after it is persisted, the transaction is replayed
   forward on recovery.
3. **Apply staged file replacements**: for each REPLACED
   or ADDED file in the transaction, atomically rename
   the staged version into place.
4. **Remove deleted files**: for each REMOVED file in the
   transaction, delete the path.
5. **Update the package database**: write the new
   package state.
6. **Invoke deduplicated side effects**: for each
   distinct side-effect identifier (§4.3) declared by any
   operation in the transaction, invoke it once.
7. **Mark the transaction journal complete**: clear the
   commit record. The transaction is fully committed.

If any step from 3 onward fails, the recovery procedure
(§7.5) replays the journal to either complete or roll
back the transaction depending on whether the commit
record was persisted in step 2.

### Journal integrity

The transaction journal MUST be stored under a security
descriptor that grants write access only to the package
manager principal. No other principal MAY write to the
journal under normal operation.

Each commit record persisted in step 2 MUST include an
HMAC or signature over the record's contents using a
key bound to the package manager principal's KACS
state. The HMAC MUST cover, at minimum:

- The set of staged file paths the transaction will
  rename into place
- The content hash (per §3.5) of each staged file as
  observed in the staging area at the moment the
  HMAC is computed
- The transaction identifier
- The commit timestamp

This binds the commit record both to the principal
that produced it AND to the exact staged bytes the
transaction will install. An attacker who can write to
the staging area (bypassing the staging-area SD)
cannot swap a staged file between commit-intent
persistence and the rename loop without invalidating
the HMAC.

In §7.4.5 step 3 (apply staged file replacements), the
package manager MUST re-verify each staged file's
content hash against the value bound by the HMAC
immediately before invoking `renameat2`. If the
re-verification fails, the transaction MUST be
considered failed and recovery (§7.5) MUST run.

The staging area MUST be stored under a security
descriptor that grants write access only to the
package manager principal.

The exact key-binding mechanism (key provisioning at
package manager install, storage) is implementation-
defined in v0.22. A future version of this specification
is expected to mandate a specific binding via PSD-004's
secret-binding facilities.

In v0.22, the binding key MUST satisfy the following:

- Each HMAC computed over a commit record MUST include
  a per-transaction nonce of at least 128 bits drawn
  from a cryptographically secure random source. The
  nonce MUST be persisted in the commit record itself.
- Each commit record MUST include a transaction-start
  timestamp captured once at the start of the
  transaction. Subsequent operations within the same
  transaction MUST reference this captured timestamp
  rather than reading the current clock, so audit
  forensics remain consistent if the system clock
  jumps mid-transaction (e.g., NTP step). The
  pre-commit audit event (§7.6.3) MUST also use the
  captured transaction-start timestamp.
- The binding key MUST be rotated when the package
  manager itself is upgraded. After rotation, journal
  entries (transaction journal and audit-retention
  journal) signed under the prior key remain valid
  for the duration needed to drain pending entries,
  after which the prior key MUST be destroyed.
- On rotation, any pending audit-retention journal
  entries (§7.6.3) MUST be re-HMAC'd under the new
  key before the prior key is destroyed; failure to
  re-HMAC the backlog before rotation MUST cause the
  rotation to abort and the package manager to
  surface the failure to the operator.
- v0.22 conformance requires that the mechanism,
  whatever it is, makes journal-entry forgery
  impossible without holding the package manager
  principal's protected key material at the time of
  forgery (i.e., historical key compromise that has
  been remediated by rotation cannot retroactively
  forge commit records, because the per-transaction
  nonce was not predictable at the time of the
  historical compromise).

> [!INFORMATIVE]
> Journal integrity protection prevents a class of
> recovery attack where an attacker writes a forged
> commit record alongside attacker-controlled staging
> content, then triggers a "crash recovery" that rolls
> the staging content forward as if it were a
> legitimate commit. The KACS-restricted SD on the
> journal directory is the primary defence; the HMAC
> on individual commit records is defence-in-depth.

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

On startup, the package manager MUST check for an
incomplete transaction journal:

1. If no journal exists or the journal is marked
   complete: no recovery needed.
2. If a journal exists with a persisted commit record
   but no completion mark: roll forward (re-apply the
   transaction's changes from the staged state).
3. If a journal exists without a persisted commit
   record: roll back (discard staged changes, restore
   the pre-transaction state).

Recovery MUST run before any new transaction is permitted.

> [!INFORMATIVE]
> Step 2 (roll forward) handles the case where the system
> crashed after committing intent but before completing
> file moves and database updates. The intent is durable;
> the system completes what was promised.
>
> Step 3 (roll back) handles the case where the system
> crashed before committing intent. From the consumer's
> perspective, the transaction simply did not happen.

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
