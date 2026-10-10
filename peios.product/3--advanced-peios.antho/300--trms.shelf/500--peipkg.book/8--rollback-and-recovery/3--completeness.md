---
title: Completeness
description: A successful rollback leaves the system indistinguishable from before the transaction — and what happens when rollback itself fails.
---

A successful rollback leaves the system indistinguishable from its state
immediately before the transaction began: file contents and existence as
before, the package database as before, and the journal carrying no
pending transaction.

Security descriptors come back with the files. A restore-by-rename
preserves a displaced original's descriptor exactly, because the file
was never rewritten. For newly created content the question does not
arise, since the file is removed rather than restored.

## When rollback itself fails

A rollback can fail: an I/O error, a filesystem gone read-only, a
permission change mid-operation. The intended behaviour is that such a
rollback is reported as a **failed rollback**, the system is treated as
indeterminate, and further transactions are prevented until an operator
resolves it.

Earlier wording here said rollback errors were discarded at every call
site and the journal closed as rolled back regardless. That is not the
reviewed cross-root path: in
[peipkg `8b588ae8`](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L668-L724),
rollback failure is reported and the affected journal remains pending.
Follow the [cross-root recovery checks](~peios/package-management/transactions-and-recovery#across-more-than-one-root)
with all participants reachable. This source correction does not establish
the behaviour of every other rollback path or every installed revision.

If inspection instead establishes the **previously described closed-journal
failure**, its consequences are:

- the failure is not reported;
- the transaction leaves the pending state, so the next invocation's
  recovery finds nothing and does not retry;
- some originals remain at their backup paths and some new files remain
  at their final paths;
- the history shows an authoritative-looking rolled-back record;
- the database and the filesystem disagree, with nothing to reconcile
  them.

`peipkg verify` can identify recorded files whose hashes no longer match
what is on disk. Use it alongside transaction state and the operation's
diagnostics; a rolled-back history label alone is not proof of restoration.
