---
title: Opening files
type: concept
description: Two paths exist for opening a file — kacs_open with an explicit desired access mask, and the legacy openat/open with POSIX flags. Both use FACS, both produce a fd with a cached granted mask, but their semantics around partial grants differ. This page covers both, plus create dispositions, MAXIMUM_ALLOWED, and the SD-at-creation rules.
related:
  - peios/file-access/overview
  - peios/file-access/the-handle-model
  - peios/file-access/managing-file-security
  - peios/file-access/special-cases
---

There are two ways to open a file in Peios. **`kacs_open`** is the native interface — the caller specifies an explicit desired access mask, and the kernel either grants all of it or fails the open. **`openat`** (and the older `open`) is the legacy POSIX interface — POSIX flags map to access masks, and the kernel uses split "core" and "compat" semantics so that rights requested but not granted can sometimes be silently dropped without failing the open.

This page covers both syscalls, the create-disposition options, the `MAXIMUM_ALLOWED` mode, and the rules around the caller supplying an SD for newly-created files.

## kacs_open — KACS-native

`kacs_open` is the canonical Peios open syscall:

```
fd = kacs_open(dirfd, path, &how, sizeof(how), &status)
```

Where `how` is a `kacs_open_how` struct:

| Field | Meaning |
|---|---|
| `desired_access` | The 32-bit mask of rights the caller wants. May include MAXIMUM_ALLOWED. |
| `create_disposition` | One of SUPERSEDE / OPEN / CREATE / OPEN_IF / OVERWRITE / OVERWRITE_IF. |
| `create_options` | Modifier flags — DIRECTORY, DELETE_ON_CLOSE. |
| `flags` | Additional flags — AT_EMPTY_PATH, AT_SYMLINK_NOFOLLOW. |
| `sd_ptr`, `sd_len` | Optional creator-supplied SD for new files. |

The kernel:

1. Resolves the path.
2. Decides whether the file exists / should exist based on `create_disposition`.
3. Runs AccessCheck with the calling token, the file's SD (or computes one for a newly-created file), and the `desired_access` mask.
4. **Strict-mode semantics**: every bit in `desired_access` must be granted. If any requested right is not granted, the open fails with `-EACCES`. There is no "partial open" — either every requested bit is in the granted mask or the operation fails entirely.
5. On success, returns the fd with the granted mask cached. If `status` was non-null, writes one of OPENED / CREATED / OVERWRITTEN / SUPERSEDED to it indicating what happened.

The strict-mode semantics are the right behaviour for native code. A caller that asks for read-and-write either gets both or fails; ambiguity is removed. The caller knows exactly what rights it has on the resulting fd because the mask is exactly what was requested.

The `MAXIMUM_ALLOWED` flag (covered below) is the exception — when set, the kernel relaxes strict mode and returns whatever rights the caller could have gotten.

## kacs_open_how — fields in detail

### desired_access

The 32-bit access mask. Standard format: object-specific bits 0–15, standard bits 16–20, special bits 24–25, generic bits 28–31. The kernel expands generic bits (GENERIC_READ, GENERIC_WRITE, etc.) using the file GenericMapping at evaluation time.

Special rights:
- `MAXIMUM_ALLOWED` (0x02000000) — request the maximum grantable mask. See below.
- `ACCESS_SYSTEM_SECURITY` (0x01000000) — the right to read or modify the SACL. Gated by SeSecurityPrivilege.

A `desired_access` of zero is rejected — the kernel does not grant a fd with no rights.

### create_disposition

Defines what to do depending on whether the file exists:

| Value | If file exists | If file does not exist |
|---|---|---|
| `SUPERSEDE` (0) | Delete and recreate. | Create. |
| `OPEN` (1) | Open. | Fail with ENOENT. |
| `CREATE` (2) | Fail with EEXIST. | Create. |
| `OPEN_IF` (3) | Open. | Create. |
| `OVERWRITE` (4) | Truncate to zero and open. | Fail with ENOENT. |
| `OVERWRITE_IF` (5) | Truncate to zero and open. | Create. |

`OPEN_IF` is the most common ("get me access to this file, creating if necessary"). `SUPERSEDE` removes the inode and creates a new one — useful for atomic-replace patterns.

### create_options

Modifier flags:

| Flag | Meaning |
|---|---|
| `DIRECTORY` (0x0001) | The target must be (or will be created as) a directory. If the disposition would create and this flag is set, a directory is created. If the disposition is open-only and the target is not a directory, fails with ENOTDIR. |
| `DELETE_ON_CLOSE` (0x0002) | The file should be deleted when the last fd referencing it is closed. Useful for temporary files. |

### flags

Path-resolution flags:

| Flag | Meaning |
|---|---|
| `AT_EMPTY_PATH` (0x1000) | The path is empty; operate on the directory referenced by `dirfd`. |
| `AT_SYMLINK_NOFOLLOW` (0x100) | Do not follow a terminal symlink. If the path resolves to a symlink, fails with ELOOP. |

### sd_ptr / sd_len

Optionally, the caller can supply a security descriptor for a newly-created file. The SD must be in self-relative format and within the standard size limit (65,535 bytes).

The rules for the creator-supplied SD:
- Permitted on a disposition that creates (CREATE, OPEN_IF when the file does not exist, OVERWRITE_IF when it does not exist, SUPERSEDE when it does not exist).
- **Rejected on open-existing branches** (OPEN, OPEN_IF when the file exists, OVERWRITE when the file exists). Supplying an SD on an existing-file path is an error (-EINVAL).
- If not supplied for a creation, the kernel synthesises an SD from the parent's inheritable ACEs and the creator's token defaults (see [Inheritance](~peios/security-descriptors/inheritance)).
- The caller must be entitled to set the owner SID — the same rule as `kacs_set_sd` (own SID or a SE_GROUP_OWNER group, or SeRestorePrivilege to override).

### status

Optional output indicating what happened:

| Value | Meaning |
|---|---|
| `OPENED` (1) | An existing file was opened. |
| `CREATED` (2) | A new file was created. |
| `OVERWRITTEN` (3) | An existing file was truncated and opened. |
| `SUPERSEDED` (4) | An existing file was deleted and a new file was created. |

This is useful for OPEN_IF / OVERWRITE_IF dispositions where the caller wants to know what happened. For non-conditional dispositions, the answer is predictable from the disposition itself.

## MAXIMUM_ALLOWED — relax strict mode

When `MAXIMUM_ALLOWED` (0x02000000) is set in `desired_access`, the kernel changes mode:

1. The `MAXIMUM_ALLOWED` flag is stripped from the desired mask.
2. AccessCheck runs in maximum-allowed mode (see [DACL evaluation](~peios/security-descriptors/dacl-evaluation)).
3. The full DACL is walked, accumulating every right the caller could have been granted.
4. The result is returned as the cached granted mask. **It is not compared to the desired mask for strict-mode purposes.**

Using `MAXIMUM_ALLOWED`, the open succeeds with whatever rights the caller could have gotten, including possibly fewer than what they "asked for". The other bits in `desired_access` are treated as a *hint* about what the caller would want — the kernel still evaluates them — but the call does not fail if the caller's actual rights are narrower.

The flag exists for tools that want to do "open with whatever access I can get" rather than "open with exactly these rights". A backup tool, for example, might want to open every file it encounters with whatever access is available rather than refusing the file because it cannot get write.

`MAXIMUM_ALLOWED` must be combined with at least one concrete data or execute bit. Calling with `MAXIMUM_ALLOWED` alone is rejected with `-EINVAL` — the kernel needs to know that *some* operation is intended, even if the specific rights are flexible.

## openat (legacy) — POSIX-compatibility

The legacy `openat` (and the older `open`) takes POSIX flags and maps them to access masks. The mapping is:

| POSIX flag | Maps to |
|---|---|
| `O_RDONLY` | `FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL | SYNCHRONIZE` (the read category from GENERIC_READ) |
| `O_WRONLY` | `FILE_WRITE_DATA | FILE_WRITE_ATTRIBUTES | FILE_WRITE_EA | READ_CONTROL | SYNCHRONIZE` |
| `O_RDWR` | `O_RDONLY` mapping ∪ `O_WRONLY` mapping |
| `O_APPEND` | Adds `FILE_APPEND_DATA` |
| `O_TRUNC` | Requires `FILE_WRITE_DATA` |
| `O_CREAT` | Sets the disposition to OPEN_IF (with the FILE_ADD_FILE right on the parent) |
| `O_EXCL` | With O_CREAT, switches the disposition to CREATE (fail if exists) |
| `O_PATH` | Special — see Special cases. The fd is not FACS-managed. |
| `O_NOFOLLOW` | Sets AT_SYMLINK_NOFOLLOW. |

So `openat(O_RDONLY)` maps to "open with FILE_READ_DATA + the rest of the read category". The kernel then runs AccessCheck for that mask.

### Core vs compat rights

The wrinkle: legacy openat uses a **core vs compat** split. The mapped rights are partitioned into:

- **Core** rights — the rights that the operation fundamentally needs. If any core right is denied, the open fails.
- **Compat** rights — rights that are conventionally granted with this POSIX flag but are not strictly necessary. If any compat right is denied, it is silently dropped from the cached mask — the open still succeeds, just with a narrower grant.

For O_RDONLY, the core right is `FILE_READ_DATA` (you cannot read without it). The compat rights are `FILE_READ_ATTRIBUTES`, `FILE_READ_EA`, `READ_CONTROL`, `SYNCHRONIZE` — these are convenient to have, but a read-only open is still meaningful without them.

The result is that legacy `open(O_RDONLY)` succeeds when FILE_READ_DATA is granted, even if the other read-category rights are not. The fd ends up with the granted subset cached.

This is the difference from `kacs_open`. `kacs_open(FILE_READ_DATA | FILE_READ_ATTRIBUTES)` requires *both* and fails if either is denied; `open(O_RDONLY)` requires FILE_READ_DATA and silently drops FILE_READ_ATTRIBUTES if it is denied.

The reasoning: POSIX applications expect open to succeed with reasonable defaults. Failing because a niche right was not granted would break compatibility. The split lets the application succeed with the rights it really needs and treat the others as bonuses.

### Why kacs_open exists

If legacy `openat` works fine for POSIX applications, why have `kacs_open`?

Two reasons:

**Precision.** New code that knows what rights it needs should be able to request them explicitly. `kacs_open` lets a service say "I need exactly these rights" and either get them or be told they are not granted. There is no silent narrowing.

**Direct SD provision.** `kacs_open` lets the caller pass an explicit SD for a newly-created file. Legacy `openat` does not — POSIX `open(O_CREAT)` uses umask-based defaults plus the parent's inheritable ACEs, with no path for the caller to specify a custom SD.

For most application code, legacy `openat` is the right tool. For services that care about exact-rights or that need explicit-SD-at-creation, `kacs_open` is the answer.

## Errors

Both syscalls can fail with:

| Error | Cause |
|---|---|
| `-EACCES` | Strict-mode access check failed (kacs_open), or core rights denied (legacy). Or a related path component is unreachable. |
| `-EEXIST` | The disposition was CREATE and the file already exists. |
| `-ENOENT` | The disposition was OPEN or OVERWRITE and the file does not exist. |
| `-ENOTDIR` | KACS_CREATE_OPT_DIRECTORY was set but the target is not a directory; or a path component is not a directory. |
| `-ELOOP` | AT_SYMLINK_NOFOLLOW was set and the path resolves to a symlink. |
| `-EINVAL` | Various — MAXIMUM_ALLOWED with no concrete bits, an invalid create_disposition, an SD on an open-existing branch, etc. |
| `-EBADF` | The dirfd is invalid. |

The error code tells you what went wrong. The kernel does not give cryptic codes; each maps to a specific named failure mode.
