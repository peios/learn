---
title: Rollback
---

Rollback is the procedure that restores the system to its
state before a transaction or before a previous package
version. This section covers two distinct rollback
scenarios:

- **Transaction rollback** (§7.5.1): undoing an in-flight
  or recently-committed transaction in response to a
  failure or user request.
- **Version rollback** (§7.5.2): user-initiated reversion
  of an installed package to a previously-installed or
  archived version, performed via the upgrade procedure.

## Transaction rollback

A transaction MUST be rollable back at any point before
its commit record is persisted (§7.4.5 step 2). Once the
commit record is persisted, the transaction is logically
committed and rollback is no longer permitted; the system
recovers forward (§7.4.7).

### When transaction rollback occurs

A transaction is rolled back when any of the following
happens before commit-intent persistence:

1. Any step in any operation within the transaction
   fails (e.g., a file's hash does not verify, disk
   space is exhausted, an SD is rejected by the kernel).
2. The user cancels the operation.
3. The package manager process terminates abnormally
   before commit (in which case rollback runs on the
   next package manager invocation per §7.4.7).

### Rollback procedure

To roll back an uncommitted transaction:

1. **Discard staged content**: remove all staged files
   from the transaction-scoped staging area.
2. **Discard pending database changes**: do not apply
   the transaction journal's pending updates to the
   package database.
3. **Restore originals**: any files that were modified or
   removed during the transaction are restored from
   transaction-scoped backups.
4. **Clear the transaction journal**: delete or mark
   abandoned the journal so subsequent operations
   proceed normally.
5. **Release the transaction lock**.

Side effects are NOT explicitly rolled back. Side effects
are idempotent (§4.3.2); if any were partially invoked
during a failed transaction, re-invoking them after the
rolled-back state is reached produces the correct final
state. The package manager MAY re-invoke the affected side
effects on rollback completion as a safety measure.

> [!INFORMATIVE]
> The transaction is designed so that side effects are
> invoked only at commit (§7.1.3). A failed transaction
> rolled back before commit will never have invoked side
> effects in the first place. The "MAY re-invoke"
> provision exists for cases where a failure occurs
> mid-commit, after some side effects have run.

### Backup retention

The transaction-scoped backup area holds copies of files
that the transaction modifies or removes. Backups are
retained until either the transaction commits (at which
point they are eligible for deletion) or the transaction
rolls back (at which point they are restored and then
deleted).

A package manager MAY retain transaction backups beyond
commit for a configured retention period to support
post-commit user-initiated rollback (§7.5.2). The
retention is operationally configured and not specified
normatively.

> [!INFORMATIVE]
> An implementation on a copy-on-write filesystem (btrfs,
> xfs with reflink support, ZFS) MAY satisfy the backup
> requirement using reflinks rather than full file copies.
> The requirement is logical preservation of the prior
> bytes; reflinks satisfy this with near-zero physical
> disk overhead. Disk-space verification (§7.1.2.2 step 2)
> MAY take advantage of this when the install target
> volume supports it.

### Rollback completeness

A successful rollback MUST leave the system in a state
indistinguishable from the state immediately before the
transaction began.

This MUST include:

- File contents and existence as before.
- File security descriptors as before.
- Package database contents as before.
- The transaction journal in a no-pending-transaction
  state.

A rollback that cannot achieve this state due to
underlying I/O errors or filesystem corruption MUST be
reported as a *failed rollback* and the system MUST be
considered to be in an indeterminate state. The package
manager SHOULD prevent further transactions until the
indeterminate state is resolved.

### Recovery from indeterminate state

When the package manager detects an indeterminate state
(failed rollback, corrupt journal, unrecoverable backup
mismatch), it MUST enter a recovery mode with the
following properties:

1. All write operations (install, upgrade, uninstall)
   MUST be refused until recovery completes.
2. Read operations (query, integrity check) MAY proceed
   but MUST surface the indeterminate-state warning in
   their output.
3. The package manager MUST produce a forensic report on
   demand, identifying:
   - The transaction journal contents (which operations
     were in flight, what the commit-record state was)
   - Files whose on-disk content does not match the
     hash recorded in the package database
   - Package database records inconsistent with the
     transaction journal
   - Any orphaned staged files or backup copies
4. The package manager MUST provide an explicit
   resolution command (e.g., `peipkg recover`) that
   accepts an operator decision: roll back the journal,
   roll forward the journal, or accept the current
   on-disk state and discard journal+backups.
5. Resolution MUST require operator authorisation per
   §7.6.6. The authorising principal MUST hold a KACS
   right that is NOT normally granted to the package
   manager principal; the specific KACS right is
   defined operationally (likely a new privilege
   coordinated with a future PSD-004 update). Recovery
   cannot be self-authorised by the package manager.
   Automatic resolution of indeterminate state is
   forbidden.

After resolution, the package manager exits recovery
mode and resumes normal operation. The forensic report
SHOULD be retained for operator audit.

### Recovery during package manager self-upgrade

When the package manager itself is being upgraded and
a transaction failure triggers recovery mode mid-
self-upgrade, the recovery binary that runs MUST be
the *previously-verified* package manager binary
(the version recorded as committed in the package
database before the in-flight upgrade began), NOT
the staged-but-uncommitted new version.

A package manager implementation MUST maintain an
immutable copy of its previously-verified binary
under a security descriptor that prevents the
package manager principal from modifying it during
self-upgrade. This recovery copy is invoked by the
system on detection of indeterminate state during
self-upgrade.

> [!INFORMATIVE]
> Without this rule, recovery during self-upgrade is
> ambiguous: the staged new binary may be the source
> of the failure being recovered from, and running
> it to perform recovery is self-defeating. Pinning
> recovery to the previously-verified binary closes
> the self-referential gap.

> [!INFORMATIVE]
> The recovery mode exists because indeterminate state
> can result from genuinely unsafe scenarios (disk
> corruption, kernel panic mid-write) where automatic
> resolution risks committing the wrong state. Requiring
> operator decision puts the responsibility where it
> belongs.

## Version rollback

Version rollback is a user-initiated operation that
reverts an installed package to a different (typically
earlier) version. It is implemented via the upgrade
procedure (§7.2) with the target version being the
desired older version.

### Procedure

A version rollback is performed by:

1. Querying the archive index (§6.3) for the available
   versions of the target package.
2. Selecting the desired older version.
3. Invoking upgrade (§7.2) with the older version as the
   "new" version. This requires explicit user
   authorisation per §7.2.5 since the operation is a
   downgrade.

The transaction is performed in the standard way (§7.4)
with the standard atomicity and crash-safety guarantees.

### Constraints

A version rollback target MUST be available from a
configured repository's archive index. Local-only
rollback (without re-fetching) is permitted only if the
archive package was previously cached.

A version rollback MAY require dependent package
adjustments if the dependent package's constraints are
not satisfied by the older version. The resolution
procedure (§4.2) determines this; the resulting plan may
include additional downgrades or removals.

### Limitations

Version rollback can only roll back to versions that the
repository archive retains (§6.3.1). Versions pruned from
the archive cannot be rolled back to without external
package files (e.g., a manually-saved `.peipkg` from a
previous backup).

Version rollback does NOT roll back changes outside the
package's payload: registry state, system configuration
materialised by reconcillers, runtime data under
`/var/`, and any user data are unaffected by package
version changes.

> [!INFORMATIVE]
> Comprehensive system rollback (including state under
> registry control) is a higher-level concern handled by
> recovery snapshots and other mechanisms outside this
> specification. Package-level version rollback is
> sufficient for the common case of "this update broke
> something; revert the package".
