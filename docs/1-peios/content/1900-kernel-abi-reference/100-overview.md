---
title: Kernel ABI reference
type: reference
description: The full surface of KACS-specific syscalls and ioctls — names, numbers, parameters, and the rules common to all of them. This page is the map for what is exposed at the kernel/userspace boundary and the conventions every interface follows.
related:
  - peios/kernel-abi-reference/syscalls
  - peios/kernel-abi-reference/token-ioctls
  - peios/kernel-abi-reference/structs-and-forward-compat
  - peios/wire-formats-reference/overview
  - peios/constants-and-catalogs/overview
---

The kernel ABI is the surface that userspace code calls into. It is the union of every syscall the Peios kernel implements — the file and process syscalls (`open`, `read`, `fork`, `exec`, `mmap`, the full POSIX surface), the KACS-specific syscalls (`kacs_*`), the KMES syscalls, the ioctls on every kind of fd. This topic's job is to document all of it.

This v0.20 pass of the documentation covers the **KACS-specific** portion in depth — every `kacs_*` syscall, every `KACS_IOC_*` ioctl on token fds, every struct that crosses the kernel boundary in those calls. The non-KACS-specific portion (the POSIX syscall surface, the standard fd ioctls, the rest) is in scope for this topic but not yet written; treat the current set of pages as a focused start, with the full ABI reference coming in subsequent passes.

The KACS-specific surface has two categories: **syscalls** (`kacs_*`) for operations on the kernel's KACS state generally, and **ioctls** (`KACS_IOC_*`) on token file descriptors for operations specific to a token. This page covers the conventions both share — the syscall number block, the ioctl magic, the universal calling rules, the forward-compatibility model. The specific syscalls and ioctls are catalogued in the following pages.

## Syscall block

KACS-specific syscalls occupy the syscall-number block **1000–1027** on x86_64. Each `kacs_*` syscall has a fixed number in this range. The full per-syscall mapping is in [Syscalls](~peios/kernel-abi-reference/syscalls).

Numbers in this range are reserved for KACS and not used by any other subsystem. The block was chosen to avoid collision with the standard Linux syscall numbering (which occupies the lower range) and to leave room for KMES (which uses a separate block).

A few notes:

- The numbers are stable. Once a syscall has been assigned a number in v0.20, that number does not change in future versions.
- New syscalls in future versions will use the next available number in the block or — if the block is exhausted — a successor block. Userspace should not assume the block ends at 1027; it ends at the last currently-assigned number.
- Syscalls beyond the assigned range return `-ENOSYS`. Standard syscall-not-found behaviour.

## Ioctl magic

Token ioctls use the magic byte `'K'` (0x4B). The full ioctl identifier follows the standard Linux ioctl format: `_IO[R/W/RW](magic, number, type)`.

The defined ioctl numbers under `'K'` are 0 through 10 in v0.20. Each is for a specific operation; the catalog is in [Token ioctls](~peios/kernel-abi-reference/token-ioctls).

Token file descriptors are the **only** fd type that responds to `'K'`-magic ioctls. Other KACS interfaces (process pidfds, socket fds, etc.) use either direct syscalls or other magic. The `'K'` magic is specifically the token-operations namespace.

## Token fd characteristics

Every token fd returned by KACS — from `kacs_open_self_token`, `kacs_create_token`, `kacs_open_process_token`, etc. — has these properties:

- **Underlying type**: anonymous inode named `kacs-token`. Visible in `/proc/<pid>/fd/<n>` as a symlink to `anon_inode:kacs-token`.
- **Open flags**: `O_CLOEXEC` set by default. The fd does not survive `exec` unless `FD_CLOEXEC` is explicitly cleared.
- **Access mask**: each fd carries an access mask (the standard `TOKEN_*` rights) that gates which operations are permitted on the fd.
- **Closable**: standard `close()` closes the fd. The underlying token's refcount drops by one; the token may or may not be destroyed depending on other references.

Token fds are inheritable across `fork` (subject to `FD_CLOEXEC`) and transferable via `SCM_RIGHTS`. The access mask is preserved in both cases.

## Byte-order conventions

All multi-byte numeric values in the KACS ABI are **little-endian** on x86_64. This matches the platform's native byte order; on a little-endian machine the encoding is identical to host order.

The one exception is in SID encoding: the `IdentifierAuthority` field of a SID (6 bytes) is **big-endian**. This is for compatibility with the SID format used in directory services and across federation boundaries. The `SubAuthority` values within a SID are little-endian.

This mixed-endianness is the SID format's choice, not a general ABI rule. Everywhere else in the ABI is uniformly little-endian.

## Pointer parameters

Several syscalls take pointers to userspace buffers (for input data, output data, or both). The conventions:

- **Userspace pointers** are passed as 64-bit values, regardless of the calling process's word size. The kernel validates that the pointer is accessible from the calling process's address space.
- **Null pointers** are typically rejected with `-EFAULT` unless the syscall specifically permits them (e.g., for probe-mode calls where a null output buffer means "tell me the size").
- **Buffer-size parameters** are typically `size_t` (or u32 in struct layouts that require fixed sizes). The kernel enforces sane upper limits to prevent unreasonable allocations.

The exact pointer conventions per syscall are documented per-syscall in [Syscalls](~peios/kernel-abi-reference/syscalls).

## Forward-compatibility model

Several KACS struct types are versioned by **size**: the struct has a `size` field at offset 0, and the kernel reads only up to whatever size the caller declares (capped at the kernel's known maximum).

The pattern:

1. Caller fills out the struct, sets `size` to the size they know about, passes a pointer.
2. Kernel reads `size` bytes (or `min(size, kernel's known size)` bytes).
3. Unknown trailing bytes (beyond the kernel's known size) must be zero. Non-zero values in unknown regions return `-EINVAL`.
4. New struct fields appended at the end in future versions get default values when older callers don't fill them.

This is the standard forward-compatibility pattern. Userspace built for an older kernel continues to work; kernel updates can add fields without breaking existing callers; new callers using new fields fail gracefully on older kernels.

The structs that use this pattern (and their v1 minimum sizes) are catalogued in [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat).

## Error codes

KACS syscalls and ioctls use the standard Linux `errno` convention: return -1 (or -errno on syscalls that don't go through libc) and set the appropriate error code.

The error codes you will see most often:

| Code | Meaning in KACS context |
|---|---|
| `-EACCES` | The access check denied the operation. The most common error from KACS. |
| `-EPERM` | A privilege required for the operation is not present, or a special restriction was triggered (e.g., restricted→unrestricted same-user impersonation). |
| `-EINVAL` | A parameter is malformed — bad SD, unknown enum value, non-zero reserved fields, etc. |
| `-EFAULT` | A pointer parameter is invalid. |
| `-ERANGE` | A buffer is too small. Often paired with the kernel writing the required size to the size parameter. |
| `-ENOENT` | A target principal/object does not exist. |
| `-EBADF` | A file descriptor is invalid. |
| `-EBUSY` | A resource is in use (rare; specific syscalls document their cases). |

Per-syscall details about which errors are possible and what each indicates are in [Syscalls](~peios/kernel-abi-reference/syscalls).

## What this reference covers

This topic is organised into three pages:

- [Syscalls](~peios/kernel-abi-reference/syscalls) — every `kacs_*` syscall, its number, parameters, return value, and possible errors.
- [Token ioctls](~peios/kernel-abi-reference/token-ioctls) — every `KACS_IOC_*` ioctl on token fds.
- [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat) — the struct layouts for syscall arguments, the size-versioning model, and the rules for handling unknown fields.

For the on-wire formats of token payloads, security descriptors, conditional ACE bytecode, and similar — those are in the [Wire formats reference](~peios/wire-formats-reference/overview) topic.

For numeric constants — well-known SIDs, privilege LUIDs, ACE types, access mask bits — see [Constants and catalogs](~peios/constants-and-catalogs/overview).

## Stability

The v0.20 ABI is committed: the syscall numbers, ioctl numbers, struct layouts, and constant values defined here are stable. Future versions of Peios will not change the meaning of an existing item.

Additions to the ABI (new syscalls, new ioctls, new constants) may happen in future versions and follow the forward-compatibility model. New struct fields are appended; new flag bits use previously-unused positions; new syscall numbers extend the block.

Programs written against the v0.20 ABI will continue to work against future kernels. Programs using features added in later versions will not work on v0.20 kernels (they will get `-ENOSYS` or `-EINVAL` for the new things).
