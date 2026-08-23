---
title: Transaction Rollback
description: Rollback is possible at any point before the database commit — when it happens, the procedure, and the order it undoes things in.
---

A transaction can be rolled back at any point before the database commit
(§7.4 step 3). After that commit the transaction is committed, and what
remains is cleanup rather than rollback.

## When it happens

1. Any step of any operation fails — a hash does not verify, disk space
   runs out, a security descriptor is rejected.
2. The operator cancels.
3. The process terminates abnormally before commit, in which case
   rollback runs on the next invocation (§7.8).

## The procedure

1. Discard the transaction's staged files.
2. Leave the pending database changes uncommitted — the commit never
   ran — and clear the transaction from the journal.
3. Restore every displaced original by renaming its backup back into
   place.
4. Remove the directories the transaction created.
5. Release the lock.

Side effects are not involved. They run only after the database commit,
so a rolled-back transaction never reached one and there is nothing to
undo.

## Ordering

File operations are reversed in the opposite order to the one they were
applied in, and each step checks the current state before acting, so a
rollback interrupted partway and re-run reaches the same result.
