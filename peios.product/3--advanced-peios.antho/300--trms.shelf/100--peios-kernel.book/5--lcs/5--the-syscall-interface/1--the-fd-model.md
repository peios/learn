---
title: The Fd Model
description: The hybrid syscall and ioctl interface — key fds, open-time checking, transaction fds, and the conventions for strings and output buffers.
---

LCS uses a hybrid syscall/ioctl interface, the same shape KACS uses
within PKM.

**Syscalls** create file descriptors: opening a key, creating a key,
beginning a transaction. There are three, numbered 1100 to 1102 in the
PKM range. **Ioctls** operate on a descriptor that already exists —
eighteen of them, all under type byte `'R'`. **`close()`** releases
both kinds of fd through the ordinary fd lifecycle.

## Key fds

A key fd is an anonymous inode created with `O_CLOEXEC`, holding:

| Field | Description |
|---|---|
| Source and key GUID | The identity of the opened key. |
| Granted access mask | Computed once by AccessCheck at open. Immutable. |
| Resolved path | After symlink resolution and `CurrentUser\` rewriting. |
| Ancestor chain | The GUID at each path component from the hive root down. Captured during the open walk, used for subtree watch dispatch (§5.6.3). |
| Watch state | Armed or not, filter, subtree flag, pending event queue. |

Key fds behave like any other fd: `close()`, close-on-exec,
`poll`/`epoll`, and passing over Unix sockets with `SCM_RIGHTS`. That
last one is what makes them capabilities (§5.4.1).

## Open-time checking

A caller names a desired access mask, and AccessCheck evaluates it
against the key's Security Descriptor. All of it is granted or the open
fails with `EACCES`. `MAXIMUM_ALLOWED` is the only way to ask for
whatever is available.

The granted mask lives on the fd, and every subsequent ioctl is a
bitmask test against it — not a fresh AccessCheck, and not a fresh read
of the descriptor.

Opening relative to a parent fd skips both path parsing and
AccessCheck for the parent portion. The caller already proved its
access when it obtained the parent fd, and this is the ordinary way to
walk a subtree.

## Transaction fds

A transaction fd is an anonymous inode holding a transaction id and,
once bound, its source and hive. Transaction lifetime is fd lifetime:
closing without committing aborts (§5.7.1).

## Reserved fields

Every syscall and ioctl argument structure uses natural C layout with
fixed-width fields and explicit padding. Nothing is packed.

Fields named `_pad`, and anything else described as reserved, are ABI
extension points. **A caller must set them to zero**, and a non-zero
reserved or padding field fails the operation with `EINVAL` — before
source dispatch, before transaction enlistment, before sequence
allocation, and before any output is copied.

In the other direction, LCS zeroes every reserved and padding byte of
an output structure or a watch event before copying it to userspace.

Flags fields carry only the bits defined for them. An unknown or
reserved flag bit is `EINVAL` unless a specific field says otherwise.

The point of all this is that a future version can give a reserved
field meaning without an older kernel having silently accepted a value
it did not understand.

## Strings

Strings in ioctl structures are **length-delimited, not
null-terminated**. Each is a `(len, ptr)` pair where `len` is a byte
count and `ptr` is a `u64` userspace address. LCS reads exactly `len`
bytes. A terminator is neither required nor expected, and one included
in the length is a null byte and therefore invalid.

Syscall paths are the exception: they arrive as null-terminated C
strings and have the terminator stripped before validation (§5.2.8).

## Variable-size output buffers

Six ioctls return variable-size data — `REG_IOC_QUERY_VALUE`,
`QUERY_VALUES_BATCH`, `ENUM_VALUES`, `ENUM_SUBKEYS`, `QUERY_KEY_INFO`
and `GET_SECURITY` — and all six use one convention.

For each output buffer described by `(length, pointer)`:

- **length 0 is a size probe**, whether the pointer is null or not. The
  pointer is not dereferenced.
- **length greater than 0** requires a non-null pointer writable for
  that many bytes, or the ioctl returns `EFAULT`.

If any output buffer is too small the ioctl returns `ERANGE` and writes
**every required size it can determine**, not just the first one that
failed — so a caller with two undersized buffers learns both sizes from
one call.

On `ERANGE`, output buffers are **not partially filled**; their
contents are unspecified. Output scalar metadata is meaningful only on
success, unless an ioctl explicitly documents a field as carrying a
required size or count on `ERANGE`.

Input pointer faults return `EFAULT`, validated before source dispatch
wherever that is possible.
