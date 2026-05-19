---
title: Error Model
---

All syscalls and ioctls use standard Linux error conventions:
syscalls return -1 and set errno; ioctls return -1 and set errno.

## Registry-specific errno semantics

| Errno | Registry meaning |
|---|---|
| ENOENT | Key or value does not exist after layer resolution. Enumeration index past end. |
| EACCES | AccessCheck denied the required access right, or the fd's granted mask lacks it. |
| EINVAL | Invalid path, invalid arguments, non-zero reserved or padding ABI field, desired_access is zero or contains unknown/reserved bits, operation on committed/aborted/closed transaction, symlink target not REG_LINK type, maximum key depth exceeded. |
| EFAULT | Userspace pointer invalid. For variable-size output buffers, non-zero length with null or non-writable pointer is invalid; zero-length output probes ignore the pointer. |
| ENAMETOOLONG | Key name component or value name exceeds MaxPathComponentLength, or total path length exceeds MaxTotalPathLength. |
| ELOOP | Symlink resolution depth exceeded. |
| ETIMEDOUT | Source did not respond within RequestTimeoutMs, or operation used a timed-out transaction fd. |
| EIO | Source returned an internal error, source is unavailable, or operation used a transaction fd whose bound source went Down. |
| ENOMEM | Kernel memory allocation failed. |
| ENOSPC | Layer cap exceeded. Value data exceeds MaxValueSize. |
| ENOTEMPTY | Cannot delete a key that has visible children. |
| EXDEV | Transaction operation targets a different hive than the transaction's bound hive. |
| EPERM | Operation requires a privilege the caller does not hold (symlink creation, layer creation at precedence > 0, layer precedence elevation, backup, restore). |
| EAGAIN | Conditional write failed -- the layer entry's sequence number did not match the expected value. Caller SHOULD re-read and retry. |
| EBUSY | Transaction could not acquire write lock, or MaxBoundTransactionsPerSource exceeded (operation that would bind a new transaction). |
| ERANGE | Caller-provided output buffer is too small. All known required sizes are written to their output length fields, and variable-size output buffers are not partially filled. Caller SHOULD retry with larger buffers. |
| EEXIST | Path entry or key already exists (duplicate creation at the source). |
| ENOTSUP | Source does not support explicit transactions (returned by the operation that would bind a transaction to that source). |
| EBADF | Fd argument is not valid or not open in the required mode (e.g., backup output fd not writable, restore input fd not readable). |
| EOVERFLOW | A source reported a persisted sequence number too large for LCS to allocate a future sequence number. |
| ESTALE | Source re-registration attempted to resume a Down source slot with stale or mismatched hive identity. |
