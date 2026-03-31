---
title: Interface Model
order: 1
---

LCS uses a hybrid syscall/ioctl model, following the pattern
established by KACS within PKM:

- **Syscalls** for operations that create file descriptors: opening
  keys, creating keys, beginning transactions. Numbered in the PKM
  range (1100+).
- **Ioctls on key fds** for operations on an already-opened key:
  reading values, writing values, deleting, enumerating, security,
  watches.
- **Ioctls on transaction fds** for transaction control (commit).
- **close()** for releasing key and transaction fds. Standard fd
  lifecycle.

## Key fds

Key fds are anonymous file descriptors (via anon_inode_getfd)
representing an open reference to a registry key. A key fd stores:

| Field | Description |
|---|---|
| Key GUID | The identity of the opened key. |
| Granted access mask | The access rights granted at open time. Immutable after open. |
| Resolved path | The path after symlink resolution and CurrentUser rewriting. |
| Ancestor chain | GUIDs at each path component from hive root to this key. Captured during path resolution at open time. Used for subtree watch dispatch. |
| Watch state | Armed/disarmed, filter, subtree flag, pending event queue. |

Key fds support standard fd semantics: close(), close-on-exec,
poll()/epoll(), passing over Unix sockets via SCM_RIGHTS.

## Open-time access checking

When a key is opened, the caller specifies a desired access mask.
LCS evaluates AccessCheck against the key's SD using the caller's
token. All requested rights MUST be granted or the open fails with
EACCES. There is no partial grant.

The special value MAXIMUM_ALLOWED requests whatever the SD grants.
This is the only way to get a "give me what I can get" fd.

The granted access mask is stored on the fd and checked on every
subsequent ioctl -- a bitmask check, not an AccessCheck
re-evaluation.

## Fd delegation

Key fds can be passed over Unix sockets via SCM_RIGHTS. A passed
key fd carries its granted access mask -- the recipient gets the
access the original opener was granted, regardless of the
recipient's own token.

This is explicit capability delegation, consistent with the Peios
model where fds are capabilities. Passing a KEY_WRITE fd to another
process gives that process write access even if its own token would
not pass AccessCheck.

Opening a key relative to a parent key fd avoids redundant path
parsing and AccessCheck for the parent portion. This is the common
case for traversing a subtree.

## Transaction fds

Transaction fds are anonymous file descriptors representing an
active transaction. A transaction fd stores the transaction ID and
source binding (determined by the first operation). Transaction
lifetime is fd lifetime: closing without committing aborts.

## Ioctl type byte

All key fd ioctls use type byte `'R'` (Registry). Transaction fd
ioctls use the same type byte.
