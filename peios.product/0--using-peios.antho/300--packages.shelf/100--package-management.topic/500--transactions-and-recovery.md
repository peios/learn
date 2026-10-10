---
title: Transactions and recovery
type: how-to
description: Distinguish an interrupted transaction from a completed change, recover pending work, verify the files, and handle documented rollback limits.
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/installing-and-removing
  - peios/package-management/named-roots
  - peios/auditing/overview
---

After an interrupted or failed package operation, inspect its history,
recover pending work, and verify what is on disk before making another change.
Use `undo` or `downgrade` only when you mean to reverse a **committed** change.

| What you see | What to do |
|---|---|
| A pending transaction after an interruption | Run `peipkg recover`, then inspect history and verify files |
| A committed update you want to reverse | Review [`undo` or `downgrade`](~peios/package-management/keeping-a-system-current) |
| A `rolled-back` record but damaged or missing files | Follow [failed-rollback checks](#when-recovery-does-not-restore-the-files); history alone is not proof of restoration |
| A committed change with a maintenance warning | Read the warning; a failed post-commit side effect does not undo the package change |
| An interrupted feature script | Use [feat recovery](~peios/features/using-feat#recover-an-interrupted-feature); package recovery does not reverse feature setup |

> [!WARNING]
> The [failed-rollback reference](~peios/peipkg/failure-modes/a-failed-rollback)
> retains an earlier closed-journal failure description: history could say
> `rolled-back` even though files were not restored. The source-verified
> [cross-root path below](#across-more-than-one-root) instead reports failed
> preparation rollback and retains the affected pending journal. Inspect
> the actual state rather than applying either description to every version.
> [Filesystem visibility](~peios/peipkg/transactions/visibility) also differs
> from database durability: files can change before package state commits.
> Do not assume a failed operation left the system unchanged or restored.

## Recovering an interrupted transaction

Use the same root as the failed operation. If it was an offline or named
root, put `--root TARGET` before each command below.

```
peipkg history
peipkg recover
peipkg history
peipkg verify
```

1. Record the transaction id, state, affected packages and error. Do not
   delete staged files or backups before recovery has had a chance to use them.
2. Run `recover`. A pending single-root transaction is rolled back; if none is
   pending, the command says so. A committed transaction has only cleanup
   left and is not reversed by `recover`.
3. Read the result and inspect history again. Recovery can itself fail.
4. Verify the affected packages, or all packages as above. Review each
   difference against intentional edits and any `.peipkg-new` file.

Ordinary install, upgrade and removal commands attempt recovery of pending
single-root work before starting new work. Explicit `recover` lets you deal
with the interruption first and produces a recovery audit event; the automatic
path does not. Read-only package queries remain available without waiting
for the transaction lock. A second writer reports `transaction in progress`;
wait for that operation to finish before trying another change.

### Across more than one root

A multi-root upgrade has one combined plan and coordinated execution; it
is not a series of independent per-root upgrades. See
[Named roots](~peios/package-management/named-roots#cascading-upgrade) for the
preparation and sequential-commit boundaries. Preparation rollback can fail;
in the reviewed source that path retains a pending journal. Do not treat it
as the older closed-journal failure described elsewhere on this page.

For recovery:

1. Retain the original named-root topology and make every participating
   root present and reachable. Run `peipkg recover` explicitly from the same
   system anchor, using the original `--root TARGET` if one was selected.
   An ordinary single-root operation refuses pending cross-root work in
   isolation. Recovery discovers reachable roots; it does not prove that a
   missing or unregistered participant has been found.
2. Read the outcome. If no participant committed, pending participants are
   rolled back. If a participant committed, pending participants are rolled
   forward using persisted completion data. Missing or malformed data causes
   refusal; a later recovery step can fail after another root was reconciled.
3. Inspect history and verify files in **every** participant. In this source,
   the CLI's **rolled back cross-root transaction** line is printed after
   either backward or forward reconciliation. It is not proof of rollback;
   the forward path records `rolled forward: cross-root recovery` in the
   transaction. Keep the diagnostics and treat any refused or unreachable
   root as unresolved.
4. Review maintenance separately. Roll-forward recovery applies persisted
   package metadata and attempts backup cleanup, but does not invoke the
   normal post-commit side-effect runner. Do not assume it re-ran `depmod`
   or `man-db`. Use the [invocation reference](~peios/peipkg/side-effects/invocation)
   to identify the affected root and kernel release, and verify the needed
   maintenance before relying on that system.

This follows peipkg `8b588ae8`'s
[CLI root discovery and report](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/recover.go#L12-L119),
[coordinated recovery decision](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L805-L917),
and [roll-forward implementation](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L773-L802).
It is a source-level contract, not evidence that recovery or maintenance
succeeded on a particular machine. Check the revision supplied by the image.
The [technical recovery chapter](~peios/peipkg/transactions/crash-recovery#cross-root-the-exception)
keeps the implementation context.

## When recovery does not restore the files

The [failure reference](~peios/peipkg/rollback-and-recovery/completeness#when-rollback-itself-fails)
retains an earlier description of a **closed-journal** failure after I/O
errors, a filesystem becoming read-only, or permissions changing. If that
is the state you actually find, another `recover` can find nothing to retry.
Do not assume all failed rollbacks have that outcome: the reviewed
[cross-root preparation rollback](#across-more-than-one-root) reports errors
and retains the affected pending journal. Inspect the transaction and tool
version before choosing the recovery path.

- Use `peipkg verify` to identify recorded files that differ or are missing.
- Inspect the affected paths for staged or backup siblings, and keep the
  evidence while deciding whether the old or new content is wanted.
- Establish why writes or restoration failed before attempting repair.
- Reconcile affected files and package records manually where necessary.
  There is no `reinstall` verb: the reference describes removal and
  installation as two transactions, or a version change and change back.
  Review dependency, feature and claim consequences before removing anything.
- Verify again after repair. A clean file check does not test services,
  feature scripts, registry state or user data.

The [indeterminate-state reference](~peios/peipkg/rollback-and-recovery/indeterminate-state)
describes proposed handling beyond the available history, recovery and file
verification tools; it does not establish a forensic-report command or a
`recover` option to accept the current filesystem as authoritative. Its older
blanket recovery wording must not override the coordinated cross-root path
above. A closed journal and a pending cross-root journal require different
responses.

## The transaction log

```
peipkg history
```

`history` prints the transactions peipkg has carried out, most recent first — each with an id, a timestamp, its state (`committed`, `rolled-back`, or `pending`), and a short summary.

```
$ peipkg history
49  2026-05-19T14:02:10Z  committed    upgrade nginx, zlib
48  2026-05-19T09:31:55Z  committed    install nginx
47  2026-05-18T22:14:03Z  rolled-back  install brokenpkg
```

| Option | Effect |
|---|---|
| `-n N` | Show at most `N` transactions. `-n 0` shows all of them. The default is `20`. |
| `--json` | Emit JSON: for each transaction its `id`, `state`, `started_at`, `summary`, and `operations`, each an `action` (`install`, `upgrade`, `downgrade`, `remove` or `claim`), the package `name`, and its `from` and `to` versions where they apply. |

The history is what [`undo`](~peios/package-management/keeping-a-system-current) reads to find the most recent transaction, and what ties a stray `*.peipkg-backup-<id>` file back to the operation that created it.

## What an interruption leaves behind

| Name | Meaning |
|---|---|
| `<name>.peipkg-staged-<id>` | Incoming content staged beside its destination |
| `<name>.peipkg-backup-<id>` | The displaced original, renamed beside its destination |

The names have no leading dot and carry the transaction id shown by
`history`. They are recovery material, not ordinary cache files. Do not
remove them just to tidy a directory after an interruption. A committed
transaction can also leave cleanup behind after a crash; use its recorded
state and the [recovery reference](~peios/peipkg/failure-modes/an-interrupted-transaction)
to distinguish the cases.

## Configuration files on upgrade

Package defaults live under `/usr/etc/`; `/etc/` is the merged configuration
view. Modified-file protection also recognises legacy package paths under
`/etc/`. It does not make `/etc/` a current package destination.

When a default is unchanged since installation, an upgrade can replace it.
When you edited it, peipkg preserves your file and writes the new default as
`<name>.peipkg-new`, with a warning. Compare and merge the changes deliberately.
The new sibling is unowned and is not removed by uninstall. The original
path can continue to appear in `verify` because its recorded hash is now the
new package's hash; that report alone does not mean your preserved edit is
corruption. See [Configuration files](~peios/peipkg/upgrade-and-removal/configuration-files).

## Side effects run after commit

A package can request a standard maintenance operation from a closed set;
it cannot supply arbitrary install-time scripts. Those maintenance steps run
after commit. A failure is reported as a warning, and the package change
stands. Read which step and root failed, then use the
[invocation and retry rules](~peios/peipkg/side-effects/invocation) for that
step. A later transaction that requests it can run it again; a warning does
not mean the cache was already repaired.

## The three phases

For operating the system, distinguish the plan you can decline, the work in
progress, and the reported outcome. A dry run previews a request without
applying package changes; it does not reserve the metadata or installed state
for a later invocation. The [commit procedure](~peios/peipkg/transactions/the-commit-procedure)
and [journal](~peios/peipkg/transactions/the-journal) describe the implementation.

## The one instant that matters

For a single-root transaction, the database commit is the durability boundary:
pending work is recovered by rollback, while committed work is not reversed
by `recover`. This boundary does not remove the failure and visibility limits
above. See [Atomicity](~peios/peipkg/transactions/atomicity) and
[Crash recovery](~peios/peipkg/transactions/crash-recovery).

## Backups make rollback free

Renaming displaced files avoids copying their contents for rollback; it does
not make restoration infallible or promise a lasting backup. The
[backup reference](~peios/peipkg/rollback-and-recovery/backups#retention)
says ordinary transaction backups are discarded at commit, while earlier
operator guidance described a retention window. Do not rely on transaction
backups for a later undo. The [undo reference](~peios/peipkg/upgrade-and-removal/downgrade-and-undo#undo)
describes resolving from archive metadata and requiring a reachable repository
or usable cache. Keep independent backups for data you must recover.

## Why this shape

Planning, journalling and a database commit support recovery; they are not a
whole-system snapshot. Package-version reversal affects the package payload,
not registry state, runtime data, user data or feature setup. The
[transaction](~peios/peipkg/transactions/scope) and
[rollback](~peios/peipkg/rollback-and-recovery/transaction-rollback) chapters
hold the implementation detail and its limits.

## Where to go next

- [Reverse a completed update](~peios/package-management/keeping-a-system-current)
- [Inspect files and ownership](~peios/package-management/inspecting-and-verifying)
- [Check named roots](~peios/package-management/named-roots)
- [Understand package audit records](~peios/peipkg/security/audit)
