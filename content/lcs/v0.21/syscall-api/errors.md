---
title: Error Model
order: 4
---

All syscalls and ioctls use standard Linux error conventions:
syscalls return -1 and set errno; ioctls return -1 and set errno.

## Registry-specific errno semantics

| Errno | Registry meaning |
|---|---|
| ENOENT | Key or value does not exist after layer resolution. Enumeration index past end. |
| EACCES | AccessCheck denied the required access right, or the fd's granted mask lacks it. |
| EINVAL | Invalid path, invalid arguments, operation on committed/closed transaction, symlink target not REG_LINK type, maximum key depth exceeded. |
| ENAMETOOLONG | Key name component or value name exceeds MaxPathComponentLength, or total path length exceeds MaxTotalPathLength. |
| ELOOP | Symlink resolution depth exceeded. |
| ETIMEDOUT | Source did not respond within RequestTimeoutMs. |
| EIO | Source returned an internal error, or source is unavailable. |
| ENOMEM | Kernel memory allocation failed. |
| ENOSPC | Layer cap exceeded. Value data exceeds MaxValueSize. |
| ENOTEMPTY | Cannot delete a key that has visible children. |
| EXDEV | Transaction operation targets a different source than the transaction's bound source. |
| EPERM | Operation requires a privilege the caller does not hold (symlink creation, layer creation at precedence > 0, layer precedence elevation, backup, restore). |
| EAGAIN | Conditional write failed -- the layer entry's sequence number did not match the expected value. Caller SHOULD re-read and retry. |
| EBUSY | Transaction could not acquire write lock, or MaxBoundTransactionsPerSource exceeded (operation that would bind a new transaction). |
| ERANGE | Caller-provided buffer is too small. The required size is written to the output length field. Caller SHOULD retry with a larger buffer. |
| EEXIST | Path entry or key already exists (duplicate creation at the source). |
| ENOTSUP | Source does not support the requested operation (e.g., explicit transactions). |
| EBADF | Fd argument is not valid or not open in the required mode (e.g., backup output fd not writable, restore input fd not readable). |
