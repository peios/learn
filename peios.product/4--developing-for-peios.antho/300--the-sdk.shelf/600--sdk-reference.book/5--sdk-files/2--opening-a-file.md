---
title: Opening a file
description: The open params struct — desired access, disposition, share mode and the rest — and what the call returns.
---

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
