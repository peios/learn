---
title: The Error Model
description: How LCS reports failure, and the two errnos worth reading closely because they mean less than they appear to.
---

Syscalls and ioctls follow the ordinary Linux convention: -1 and
`errno`. The errno is the whole interface — source-specific error
detail is never surfaced to a caller.

| Errno | What it means here |
|---|---|
| `ENOENT` | A key or value does not exist after layer resolution; an enumeration index is past the end; a named layer is not in the layer table; a namespace operation on an orphaned key. |
| `EACCES` | AccessCheck denied a right, the fd's granted mask lacks it, or layer write authorization failed. |
| `EINVAL` | An invalid path or argument; a non-zero reserved or padding field; a zero or unknown-bit `desired_access`; an operation on a committed, aborted or closed transaction; a symlink target that is not `REG_LINK`; maximum key depth exceeded; delete or hide on a hive root. |
| `EFAULT` | An invalid userspace pointer. A zero-length output probe ignores its pointer; a non-zero length with a null or unwritable pointer does not. |
| `ENAMETOOLONG` | A key or value name exceeds `MaxPathComponentLength`, or a path exceeds `MaxTotalPathLength`. |
| `ELOOP` | The symlink resolution depth limit was exceeded. |
| `ETIMEDOUT` | The source did not answer within `RequestTimeoutMs`, or a timed-out transaction fd was used. |
| `EIO` | The source failed, is unavailable, returned malformed data, or a transaction's bound source went Down. |
| `ENOMEM` | Kernel allocation failure. |
| `ENOSPC` | A layer cap was exceeded, or value data exceeds `MaxValueSize`. |
| `ENOTEMPTY` | A key with visible children cannot be deleted. |
| `EXDEV` | An operation targeted a different hive from the one its transaction is bound to. |
| `EPERM` | A privilege the caller does not hold: symlink creation, creating or raising a layer above precedence 0, backup, restore. |
| `EAGAIN` | A conditional write failed — the layer entry's sequence did not match. Re-read and retry. |
| `EBUSY` | A commit could not take the source's write lock, or `MaxBoundTransactionsPerSource` or `MaxReadOnlyTransactionsPerSource` was exceeded. |
| `ERANGE` | An output buffer is too small. Every determinable required size is written; buffers are not partially filled. Retry with larger ones. |
| `EEXIST` | A path entry or key already exists at the source. |
| `ENOTSUP` | The source does not support the transaction mode being requested. |
| `EBADF` | An fd argument is not valid or not open in the required mode — a backup output fd that is not writable, a restore input fd that is not readable. |
| `EOVERFLOW` | A counter cannot advance: a source reported a persisted sequence number too large to allocate past, a hive generation saturated, restore sequence remapping would overflow, or transaction ids are exhausted. |
| `ESTALE` | A source re-registration tried to resume a Down slot with a mismatched hive identity. |

## Two errnos worth reading closely

**`ETIMEDOUT` means "may or may not have happened."** If the deadline
expired before an in-flight RSI slot was reserved, no request was sent
at all. If it expired after dispatch, the source may still apply the
operation and answer later, and LCS will apply the kernel-side effects
when it does (§5.8.5). A caller that needs certainty checks state
before retrying. The same applies to a transaction commit.

**`EEXIST` is rarer than it looks.** It never comes out of
`reg_create_key`, which retries a losing race as an open (§5.5.2). From
`REG_IOC_RESTORE` it arrives only by propagation: the source answers
`RSI_ALREADY_EXISTS` while the stream is being replayed. There is no
kernel-side pre-check that a non-root GUID in a backup already exists
outside the subtree being replaced, so a collision is detected during
the restore rather than before it — inside the restore transaction,
which then rolls back (§5.9.3). Its other source is source
registration, where a hive identity collides with an **Active** slot;
a collision with a Down slot yields `EINVAL` or `ESTALE` instead
(§5.8.2).
