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

What happens is different. Rollback errors are discarded at every site
that triggers one, and the journal's transaction is then closed as
rolled back regardless.

The consequences are worth stating plainly. If a rollback fails partway:

- the failure is not reported;
- the transaction leaves the pending state, so the next invocation's
  recovery finds nothing and does not retry;
- some originals remain at their backup paths and some new files remain
  at their final paths;
- the history shows an authoritative-looking rolled-back record;
- the database and the filesystem disagree, with nothing to reconcile
  them.

`peipkg verify` will report the affected files as modified, because
their recorded hashes no longer match what is on disk. That is the only
signal.
