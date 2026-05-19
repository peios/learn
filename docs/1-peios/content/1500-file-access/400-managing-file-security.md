---
title: Managing file security
type: concept
description: File SDs are read and written via kacs_get_sd and kacs_set_sd. Both take a security_information bitmask saying which SD components to access — OWNER, GROUP, DACL, SACL, LABEL. The xattr layer is never the path; direct xattr operations on the SD are unconditionally denied. This page covers the syscalls, the access rules, and the special LABEL_SECURITY_INFORMATION flag.
related:
  - peios/file-access/overview
  - peios/file-access/the-handle-model
  - peios/file-access/opening-files
  - peios/security-descriptors/overview
  - peios/security-descriptors/ownership
---

Reading and writing a file's security descriptor is done through two dedicated syscalls — **`kacs_get_sd`** and **`kacs_set_sd`** — not through the xattr layer. Direct xattr access to the SD storage (the `security.peios.sd` or `system.ntfs_security` xattr) is unconditionally denied; the only way through is the syscall pair.

This page covers the syscalls, the `security_information` bitmask that decides which SD parts are accessed, the access rules, and the special `LABEL_SECURITY_INFORMATION` flag for setting the integrity label specifically.

## Why the xattr layer is denied

You might expect that the SD, stored in an xattr, would be readable and writable through the standard `getxattr` / `setxattr` syscalls. It is not. The kernel refuses every xattr operation on the SD xattr regardless of who is asking and what they hold.

The reasoning:

- **Atomic semantics.** Reading or writing the SD via xattr would expose the raw bytes; tools could read a partial SD (during a write by someone else), or write an SD whose internal structure is inconsistent with the file's other state.
- **Access rule unification.** The SD has its own access rules — `READ_CONTROL` to read, `WRITE_DAC` / `WRITE_OWNER` / `ACCESS_SYSTEM_SECURITY` to write different parts. Routing through `kacs_get_sd` / `kacs_set_sd` puts these rules in one place; routing through xattr would require duplicating them at the xattr layer.
- **Format flexibility.** Different filesystems store the SD differently. The syscall abstraction lets the kernel translate; the xattr layer would force a specific format.

So the syscall pair is the only path. Reading or writing the SD goes through them; xattr operations on the SD xattr are denied.

## kacs_get_sd

The read syscall:

```
size = kacs_get_sd(dirfd, path, security_info, buf, buf_len, flags)
```

Returns the SD bytes for the requested components.

| Parameter | Meaning |
|---|---|
| `dirfd`, `path` | The file to read. Standard dirfd-relative resolution. |
| `security_info` | A bitmask saying which components to return. See below. |
| `buf`, `buf_len` | Output buffer. |
| `flags` | AT_EMPTY_PATH (use dirfd as fd-relative), AT_SYMLINK_NOFOLLOW (don't follow terminal symlink). |

The kernel:

1. Resolves the path.
2. Runs AccessCheck — the caller needs the access rights corresponding to the requested components (covered below).
3. Reads the file's SD from its filesystem-native storage.
4. Constructs a **subset SD** containing only the requested components. Other components have offset 0 in the header and the corresponding PRESENT bit is clear.
5. Returns the subset SD in `buf`, with the total length as the return value.

### Probe mode

Calling with `buf_len = 0` (or `buf` = NULL) is a **probe** — the kernel computes the size the SD would take and returns it without writing to the buffer. The probe returns the same size value that a non-probe call would; the caller can use this size to allocate exactly the right buffer.

The probe call always returns the size on success. It does **not** return `-ERANGE` — the probe is itself a question about size, and answering it is the kernel's job. `-ERANGE` would be the wrong signal for a deliberate probe.

A non-probe call with `buf_len < required` returns `-ERANGE` with the required size written somewhere accessible (typically the same length parameter, or via a separate output). The caller can then reallocate and retry.

### Access rules

Different components need different rights:

| Requested component (via `security_info` flag) | Required right |
|---|---|
| `OWNER_SECURITY_INFORMATION` (0x01) | `READ_CONTROL` |
| `GROUP_SECURITY_INFORMATION` (0x02) | `READ_CONTROL` |
| `DACL_SECURITY_INFORMATION` (0x04) | `READ_CONTROL` |
| `SACL_SECURITY_INFORMATION` (0x08) | `ACCESS_SYSTEM_SECURITY` |
| `LABEL_SECURITY_INFORMATION` (0x10) | `READ_CONTROL` (the integrity label is in the SACL but its read is gated by READ_CONTROL, not ACCESS_SYSTEM_SECURITY) |

`READ_CONTROL` is the standard "read SD" right and is implicitly granted to the owner. `ACCESS_SYSTEM_SECURITY` is gated by `SeSecurityPrivilege` — the SACL is read-restricted to administrators with the privilege.

A caller asking for components they do not have rights for gets `-EACCES`. A caller asking for a mix can succeed for the components they can access — but the kernel does this as an all-or-nothing operation: if any requested component fails its access check, the whole call fails.

For combining requested components: just OR the flags. `kacs_get_sd(..., OWNER | DACL, ...)` returns owner and DACL but not SACL or group.

### SACL and LABEL are mutually exclusive

`SACL_SECURITY_INFORMATION` and `LABEL_SECURITY_INFORMATION` cannot be combined in one call. Setting both flags returns `-EINVAL`. The reasoning: `LABEL_SECURITY_INFORMATION` is a focused query for just the integrity label (which lives in the SACL); it has different access requirements than reading the full SACL. The kernel keeps the two paths separate.

## kacs_set_sd

The write syscall:

```
result = kacs_set_sd(dirfd, path, security_info, sd_buf, sd_len, flags)
```

| Parameter | Meaning |
|---|---|
| `dirfd`, `path` | Target file. |
| `security_info` | Which components to update. |
| `sd_buf`, `sd_len` | The new SD bytes (self-relative format). |
| `flags` | AT_EMPTY_PATH, AT_SYMLINK_NOFOLLOW. |

The kernel:

1. Resolves the path.
2. Parses the SD blob. Rejects malformed SDs (size limit, bad ACL structure, etc.) with `-EINVAL`.
3. Runs AccessCheck for the required rights per the components being updated.
4. Validates additional rules — owner SID is the caller's own or a SE_GROUP_OWNER group (unless SeRestorePrivilege), MANDATORY-flagged resource attributes are not removed (unless SeTcbPrivilege), integrity label is not raised above caller's own (unless SeRelabelPrivilege).
5. Writes the SD to the file's native storage.
6. Returns 0 on success.

The write is atomic: either all requested components are updated or none are.

### Access rules for writes

| Component | Required right |
|---|---|
| Owner | `WRITE_OWNER` (plus the owner SID validation) |
| Group | `WRITE_OWNER` |
| DACL | `WRITE_DAC` |
| SACL | `ACCESS_SYSTEM_SECURITY` |
| LABEL (integrity label only) | `WRITE_OWNER` (plus integrity constraint) |

`WRITE_DAC` is the standard "modify DACL" right, implicitly granted to the owner. `WRITE_OWNER` is needed to change the owner field (and the validation rules apply per [Ownership](~peios/security-descriptors/ownership)). `ACCESS_SYSTEM_SECURITY` is the SACL gate.

### The integrity label

`LABEL_SECURITY_INFORMATION` (0x10) is the focused write path for setting just the integrity label. The label lives in the SACL as a `SYSTEM_MANDATORY_LABEL_ACE`, but setting it via this flag is treated as a separate operation from setting the full SACL — with different access requirements:

- The right needed is `WRITE_OWNER`, not `ACCESS_SYSTEM_SECURITY`.
- The caller cannot raise the integrity label above the calling token's own integrity level (without `SeRelabelPrivilege`).
- Lowering the integrity label to at or below the caller's own integrity level is allowed.

`LABEL_SECURITY_INFORMATION` and `SACL_SECURITY_INFORMATION` cannot be combined in one call — same rule as for reading.

The use case: a process that wants to lower its files' integrity labels without holding `SeSecurityPrivilege`. The label is in the SACL conceptually, but setting it gets the `WRITE_OWNER` gate rather than the SACL gate, because adjusting the label down is a less sensitive operation than rewriting the audit policy.

### SD parsing and validation

The provided SD blob must be:

- In self-relative format (`SE_SELF_RELATIVE` flag set in control bits).
- Within the 65,535-byte size limit.
- Internally consistent — the offsets in the header point to valid locations, the ACLs parse cleanly, the SIDs are well-formed.

Any failure of validation returns `-EINVAL`. The original SD on the file is unchanged.

### Setting only some components

The `security_information` flags tell the kernel which components of the provided SD to apply. A blob containing owner + DACL with only `DACL_SECURITY_INFORMATION` set updates only the DACL; the file's existing owner is preserved.

The blob structure must still be valid — components not being applied are typically absent (offset 0, PRESENT bit clear) in the blob, but the blob's header still needs to be a valid SD header.

This is the pattern for updating one part of an SD without touching the others. Read the SD (probe + fetch), update the relevant component, write back with only that component's flag set.

### Ownership transfer rules

Setting the owner via `kacs_set_sd` triggers the rules described in [Ownership](~peios/security-descriptors/ownership):

- The new owner must be the caller's own user_sid, **or** a SID in the caller's groups with `SE_GROUP_OWNER` set, **or** the caller must hold `SeRestorePrivilege`.
- The caller must have `WRITE_OWNER` on the object, or hold `SeTakeOwnershipPrivilege`.

A failure here returns `-EACCES`.

The same rules apply whether you set ownership via `OWNER_SECURITY_INFORMATION` alone or in combination with other components.

## What about file mode (the POSIX rwx bits)?

The traditional POSIX file mode — `chmod`-style read/write/execute bits — does not exist in the same way under FACS. The Linux mode bits are stored alongside the SD as filesystem metadata (the inode's mode field), but they are **not consulted by FACS for access control**. The DACL is what decides access; the mode is informational only.

The kernel does still update the mode field when an SD is set (to maintain compatibility with tools that read the mode, like `ls -l`), but the mode is derived from the SD's DACL rather than being authoritative.

In particular:

- `fchmod()` is denied on FACS-managed fds. To change permissions you call `kacs_set_sd` with a new DACL.
- `chmod()` is allowed at the syscall level but the kernel translates it to an attempt to modify the SD, which goes through the usual access check.
- The mode bits in `stat()` results reflect the synthesised mode derived from the DACL, not a separate authoritative value.

This is the cleanest way to layer KACS on top of Linux file systems while preserving compatibility with tools that consult the mode. The mode is a derived view; the SD is the truth.

## Errors

Common errors from both syscalls:

| Error | Cause |
|---|---|
| `-EACCES` | Access check failed for the requested components. |
| `-EINVAL` | Malformed SD blob, invalid security_information combination, size limit exceeded, or other validation failure. |
| `-EPERM` | Owner SID validation failed without SeRestorePrivilege, or integrity label too high without SeRelabelPrivilege, or attempted MANDATORY attribute removal without SeTcbPrivilege. |
| `-ERANGE` | (`kacs_get_sd` only) Buffer too small; required size returned. |
| `-ENOENT` | The target path does not exist. |
| `-ELOOP` | AT_SYMLINK_NOFOLLOW and the path is a symlink. |

Most failures are diagnostic and clear from the error code.
