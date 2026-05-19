---
title: Rollback
---

Rollback is the procedure that restores the system to its
state before a transaction or before a previous package
version. This section covers two distinct rollback
scenarios:

- **Transaction rollback** (§7.5.1): undoing an in-flight
  (uncommitted) transaction in response to a failure or
  cancellation.
- **Version rollback** (§7.5.2): user-initiated reversion
  of an installed package to a previously-installed or
  archived version, performed via the upgrade procedure.

## Transaction rollback

A transaction can be rolled back at any point before the
database commit (§7.4.5 step 3). Once that commit
succeeds the transaction is committed and rollback no
longer applies; recovery from that point is clean-up only
(§7.4.7).

### When transaction rollback occurs

A transaction is rolled back when any of the following
happens before the database commit:

1. Any step in any operation within the transaction
   fails (e.g., a file's hash does not verify, disk
   space is exhausted, an SD is rejected by the kernel).
2. The user cancels the operation.
3. The package manager process terminates abnormally
   before commit (in which case rollback runs on the
   next package manager invocation per §7.4.7).

### Rollback procedure

To roll back an uncommitted transaction:

1. **Discard staged content**: remove the transaction's
   staged files.
2. **Discard pending database changes**: the journal's
   pending transaction is left uncommitted (the database
   commit, §7.4.5 step 3, never ran) and is cleared from
   the journal.
3. **Restore originals**: for every file the transaction
   displaced, rename its backup back into place
   (§7.5.1.3).
4. **Release the transaction lock**.

Side effects are not involved in rollback. Side effects
run only after the database commit (§7.4.5 step 4); a
rolled-back transaction never reached that commit, so no
side effect of it ever ran and there is nothing to undo.

### Backups

A backup is made by **renaming the displaced original
aside within its own directory** (§7.2 step 4, §7.3 step
3) — not by copying it. The old file's content is
retained in place under a different name, so a backup
costs no additional disk space and is produced by a
single atomic rename. The journal's backup map records,
for each displaced file, the path its backup was renamed
to.

A backup is restored — on rollback — by renaming it back
into place, and discarded — on successful commit — by
deleting it.

A package manager MAY retain backups *beyond* commit, for
a configured retention window, to support post-commit
operator-initiated rollback (§7.5.2). The window — for
example a number of recent transactions, or an age — is
operationally configured and not specified normatively.

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
   - The journal's pending transaction (which operations
     were in flight)
   - Files whose on-disk content does not match the
     hash recorded in the package database
   - Package database records inconsistent with the
     journal
   - Any orphaned staged files or backups
4. The package manager MUST provide an explicit
   resolution command (e.g. `peipkg recover`) that
   accepts an operator decision: roll the pending
   transaction back, or accept the current on-disk state
   and discard the journal and backups.
5. Resolution MUST be a deliberate operator action and
   MUST NOT be performed automatically — automatic
   resolution of an indeterminate state is forbidden.

> [!INFORMATIVE]
> The intended end state is for recovery resolution to
> require an authorisation distinct from ordinary install
> authority — a dedicated KACS right held by a
> recovery-class operator, validated by KACS. That
> mechanism depends on KACS primitives not yet specified;
> until they exist, "deliberate operator action" means
> the operator explicitly invoking the resolution command
> and confirming the chosen outcome. The package manager
> holds no principal of its own (§7.6) and cannot
> self-authorise in any case.

After resolution, the package manager exits recovery
mode and resumes normal operation. The forensic report
SHOULD be retained for operator audit.

### Recovery and package-manager self-upgrade

Upgrading the package manager is not a special case for
recovery. The package-manager binary is one file among a
transaction's payload, backed up by rename like any other
(§7.5.1.3); "recovery" reconciles a transaction that
crashed between its atomic steps, not a half-written
binary — the binary swap is itself a single atomic
rename.

The only wrinkle is that, after a self-upgrade, the
binary running the next recovery may be a different
version from the one that started the transaction. This
is handled by **versioning the journal format**: any
package-manager version that can read a pending
transaction's journal schema recovers it directly; a
version that cannot defers to manual recovery mode
(§7.5.1.5). No dedicated "immutable previous-binary copy"
is required — if recovery needs the prior binary, it is
already present as that binary's ordinary backup
(§7.5.1.3).

> [!INFORMATIVE]
> A package-manager upgrade that commits *successfully*
> but installs a defective binary is not a recovery case
> — there is no incomplete transaction. It is handled by
> running the prior binary, retained as the transaction's
> backup, by its path to perform an ordinary downgrade.

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
