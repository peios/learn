---
title: file.h — File security
type: reference
description: Complete reference for <peios/file.h> — the native KACS file open, reading and writing a file's security descriptor by path or fd, and the superblock mount-policy controls.
related:
  - peios-sdk/reference/security
  - peios-sdk/reference/access
  - peios/file-access/overview
  - peios/mount-policies/overview
---

`<peios/file.h>` is the file surface of KACS. Where ordinary POSIX `open()` gives you a file descriptor governed by mode bits, `peios_file_open` performs a **native** KACS open — an `NtCreateFile`-shaped call carrying a desired access mask, a create disposition, create options, and an optional creator security descriptor — and hands back an ordinary Linux file fd whose **granted access mask is fixed for the fd's lifetime**. Because the grant is baked into the fd, it can be delegated safely by `dup`, `SCM_RIGHTS`, or across `exec`: whoever holds the fd holds exactly the access it was opened with, no more.

Alongside the open, this module reads and writes a file's security descriptor (by path or by fd) and governs how a superblock without native SD storage is treated.

The wire constants (`KACS_DISPOSITION_*`, `KACS_CREATE_OPT_*`, `KACS_FILE_*`, `KACS_SECINFO_*`, `KACS_MOUNT_POLICY_*`, `KACS_STATUS_*`) come from `<pkm/file.h>` and `<pkm/sd.h>`. The security descriptors these calls exchange are built and parsed with [`<peios/security.h>`](~peios-sdk/reference/security).

## Opening a file

```c
struct peios_open_params {
    uint32_t    desired_access; /* KACS_FILE_* | standard | generic (strict-mode) */
    uint32_t    disposition;    /* KACS_DISPOSITION_* */
    uint32_t    options;        /* KACS_CREATE_OPT_* */
    uint32_t    flags;          /* AT_SYMLINK_NOFOLLOW | KACS_BACKUP_INTENT | KACS_RESTORE_INTENT */
    const void *sd;             /* creator SD on create, else NULL */
    size_t      sd_len;
};

int peios_file_open(int dirfd, const char *path,
                    const struct peios_open_params *p, uint32_t *status_out);
```

`peios_file_open` opens `path` relative to `dirfd` (the usual `*at` convention — an absolute path ignores `dirfd`, and `AT_FDCWD` means the current directory). It returns a file fd, or `-1` with `errno`.

The parameters:

| Field | Meaning |
|---|---|
| `desired_access` | The access mask you are requesting — `KACS_FILE_*` object rights, standard rights, or (in strict mode) generic bits the file class maps. The granted subset is what the returned fd is fixed at. |
| `disposition` | What to do about existence: `KACS_DISPOSITION_*` — open-existing, create-new, open-or-create, supersede, overwrite, and so on. This is the create/open decision `open()` splits across `O_CREAT`/`O_EXCL`/`O_TRUNC`. |
| `options` | `KACS_CREATE_OPT_*` create options — directory-vs-file, no-follow, write-through, delete-on-close, and the rest of the `NtCreateFile` option set. |
| `flags` | `AT_SYMLINK_NOFOLLOW`, plus the privilege-intent flags `KACS_BACKUP_INTENT` / `KACS_RESTORE_INTENT` that let `SeBackupPrivilege` / `SeRestorePrivilege` widen the access the open is granted. |
| `sd` / `sd_len` | The **creator** security descriptor — the SD to stamp on a newly created file. Pass `NULL` when opening an existing file (or to let the parent's inheritance decide the new file's SD). |

`status_out`, if non-`NULL`, receives a `KACS_STATUS_*` code telling you *what happened* — whether the file was opened, created, superseded, overwritten. This is how you distinguish "created a new file" from "opened the existing one" after an open-or-create disposition, without a separate `stat` race.

Errors: `EACCES` (a requested right denied — strict mode), `EEXIST` (create-new and the file exists), `ENOENT` (open-existing and it doesn't), `ENOTDIR` (directory option, non-directory target), `ELOOP` (no-follow and the target is a symlink), `EINVAL` (`MAXIMUM_ALLOWED` without a concrete data/execute bit, malformed creator SD, `NULL` `path`/`p`, `sd == NULL` with `sd_len != 0`), `EBADF` (bad `dirfd`).

```c
struct peios_open_params p = {
    .desired_access = KACS_FILE_READ_DATA | KACS_FILE_WRITE_DATA,
    .disposition    = KACS_DISPOSITION_OPEN_IF,   /* open or create */
    .options        = 0,
    .sd             = creator_sd, .sd_len = creator_sd_len,
};
uint32_t status = 0;
int fd = peios_file_open(AT_FDCWD, "data.bin", &p, &status);
if (fd < 0) { /* errno */ }
/* status == KACS_STATUS_CREATED or KACS_STATUS_OPENED */
```

libpeios marshals these params into a `struct kacs_open_how` for you — setting its size and zeroing the reserved fields — so the call stays forward-compatible across kernel versions.

## Reading and writing a file's security descriptor

A file's SD can be accessed **by path** or **by fd**. In both cases `secinfo` is a mask of `KACS_SECINFO_*` bits selecting which components (owner, group, DACL, SACL, …) the operation touches — you read or write just the parts you name and leave the rest alone.

The rights required scale with the components you touch (see [Managing file security](~peios/file-access/managing-file-security)):

| Component (`KACS_SECINFO_*`) | Reading needs | Writing needs |
|---|---|---|
| `OWNER` / `GROUP` | `READ_CONTROL` | `WRITE_OWNER` (plus owner-SID validation) |
| `DACL` | `READ_CONTROL` | `WRITE_DAC` |
| `SACL` | `ACCESS_SYSTEM_SECURITY` | `ACCESS_SYSTEM_SECURITY` |
| `LABEL` | `READ_CONTROL` | `WRITE_OWNER` (the label cannot rise above the caller's integrity without `SeRelabelPrivilege`) |

`ACCESS_SYSTEM_SECURITY` is itself gated by `SeSecurityPrivilege`; `READ_CONTROL` and `WRITE_DAC` are implicitly granted to the owner. `SACL` and `LABEL` cannot be combined in one call (`EINVAL`). The check is all-or-nothing: if any requested component fails its check, the whole call fails.

### By path

```c
ssize_t peios_file_get_sd(int dirfd, const char *path, uint32_t secinfo,
                          void *buf, size_t cap, uint32_t at_flags);
int     peios_file_set_sd(int dirfd, const char *path, uint32_t secinfo,
                          const void *sd, size_t len, uint32_t at_flags);
```

- `peios_file_get_sd` reads the `secinfo`-selected components of `path`'s SD into `buf`, getxattr-style ([two-call protocol](~peios-sdk/getting-started/library-conventions#the-two-call-buffer-protocol) — probe with `cap == 0`, and a too-small non-zero buffer fails `ERANGE` without truncating). `at_flags` accepts `AT_SYMLINK_NOFOLLOW`. Errors: `EACCES` (component right missing), `EINVAL` (`SACL` + `LABEL` together; `NULL` path, or `NULL` buffer with non-zero `cap`), `ERANGE` (non-probe buffer too small), `ENOENT` (path doesn't exist), `ELOOP` (no-follow and symlink).
- `peios_file_set_sd` writes the `secinfo` components of `sd` onto `path`, **preserving the components you did not select**. So to change only the DACL, build an SD with a DACL, pass `secinfo = KACS_SECINFO_DACL`, and the owner/group/SACL are untouched. Errors: `EACCES` (component right missing), `EPERM` (owner-SID validation failed without `SeRestorePrivilege`; label raised without `SeRelabelPrivilege`; MANDATORY attribute removed without `SeTcbPrivilege`), `EINVAL` (malformed SD, `SACL` + `LABEL` together, `NULL` or zero-length `sd`), `ENOENT`, `ELOOP`.

### By fd

```c
ssize_t peios_fd_get_sd(int fd, uint32_t secinfo, void *buf, size_t cap);
int     peios_fd_set_sd(int fd, uint32_t secinfo, const void *sd, size_t len);
```

The same operations against the object `fd` already refers to. The access check they perform depends on the fd type: a normal file fd is checked against its **cached granted mask** (the one baked in at open), while an `O_PATH`, pidfd, or token fd triggers a **live** check. That distinction — cached for the fixed-grant file fd, live for the others — is documented in PSD-004 §11.5; the practical upshot is that a file fd already opened with the right access can get/set its SD without a second path resolution.

The required rights and errors match the by-path calls, minus the path-resolution failures (`ENOENT`/`ELOOP`), plus `EBADF` (bad fd).

## Mount policy

Not every filesystem can store native security descriptors. The **mount policy** governs how KACS treats a superblock that has no native SD storage — whether files there get a synthesised SD, a template SD, or are denied. These calls target the superblock the object `fd` lives on and require `SeTcbPrivilege`.

```c
struct peios_mount_policy {
    uint32_t    policy;      /* KACS_MOUNT_POLICY_* */
    uint32_t    flags;
    uint32_t    generation;
    const void *template_sd;
    size_t      template_sd_len;
};

int peios_mount_get_policy(int fd, struct peios_mount_policy *out,
                           void *tmpl_buf, size_t tmpl_cap);
int peios_mount_set_policy(int fd, const struct peios_mount_policy *p);
```

- `peios_mount_get_policy` reads the policy for `fd`'s superblock into `out`. The template SD is returned into your `tmpl_buf` getxattr-style: on success `out->template_sd` points **into `tmpl_buf`** when that buffer was large enough, or is `NULL` if the superblock has no template. A `NULL` template buffer (or `tmpl_cap == 0`) is valid only when you don't need the template bytes. A too-small template buffer is **not** an error — the call still succeeds, reports the true length in `out->template_sd_len`, and leaves `out->template_sd` `NULL` so you can size a retry. Errors: `EPERM` (`SeTcbPrivilege` missing), `EBADF` (bad fd), `EINVAL` (`NULL` `out`, or `NULL` `tmpl_buf` with non-zero `tmpl_cap`), `EFAULT` (bad buffer pointer), `ENOMEM` (allocation failed).
- `peios_mount_set_policy` installs `p` as the superblock's policy. `policy` is a `KACS_MOUNT_POLICY_*` value; `template_sd`/`template_sd_len` supply the template SD when the policy calls for one. `flags` and `generation` must be zero on set — the kernel manages the generation counter itself and rejects a non-zero input. Errors: `EPERM` (`SeTcbPrivilege` missing), `EINVAL` (unknown or unmanaged `policy`, non-zero `flags`/`generation`, malformed or oversized template, `NULL` template with non-zero length), `EOPNOTSUPP` (superblock not KACS-managed), `EBADF` (bad fd), `EFAULT` (bad pointer).

## The generic mapping

```c
extern const struct kacs_generic_mapping peios_file_generic_mapping;
```

The canonical generic→specific rights mapping for the **file** object class. Pass it to [`peios_access_map_generic`](~peios-sdk/reference/security#access-masks), or as the `mapping` in a [`peios_access_request`](~peios-sdk/reference/access#the-request) when checking access against a file's SD — for example to pre-flight whether a caller could open a file before you actually open it.

## See also

- **[`<peios/security.h>`](~peios-sdk/reference/security)** — building the creator SDs and parsing the SDs these calls return.
- **[`<peios/access.h>`](~peios-sdk/reference/access)** — evaluating a file SD with `peios_file_generic_mapping`.
- **[File access](~peios/file-access/overview)** and **[Mount policies](~peios/mount-policies/overview)** — the operator-side model of native file security.
