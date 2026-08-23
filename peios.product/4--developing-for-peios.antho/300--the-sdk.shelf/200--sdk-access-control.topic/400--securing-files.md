---
title: Securing files
type: how-to
description: Open files the native KACS way, and read and write a file's security descriptor by path or by fd.
related:
  - peios/sdk-files/file-h-file-security
  - peios/sdk-security/security-h-security-descriptors
  - peios/file-access/overview
---

Peios files carry real security descriptors, and the SDK opens them with a native KACS open rather than POSIX `open()`. This guide covers the two everyday tasks: opening a file with a specific access, and reading or changing a file's security. The full surface is in [`file.h`](~peios/sdk-files/file-h-file-security).

To keep the fragments readable, most error checks are elided here — every call below returns `-1` with `errno` on failure, and real code must check each one (see [Library conventions](~peios/sdk-conventions/library-conventions)).

## The native open

[`peios_file_open`](~peios/sdk-files/file-h-file-security#opening-a-file) is shaped like `NtCreateFile`: you state the access you want, what to do about existence (the *disposition*), any create options, and — when creating — the security descriptor to stamp on the new file. It returns an ordinary Linux fd whose **granted access is fixed for the fd's lifetime**, which means you can safely hand it to another process by `SCM_RIGHTS`, `dup`, or across `exec`: the fd carries exactly the access it was opened with.

Open-or-create a file, readable and writable, stamping a creator SD if it's new:

```c
struct peios_open_params p = {
    .desired_access = KACS_FILE_READ_DATA | KACS_FILE_WRITE_DATA,
    .disposition    = KACS_DISPOSITION_OPEN_IF,   /* open existing, else create */
    .sd             = creator_sd, .sd_len = creator_sd_len,   /* used only on create */
};

uint32_t status = 0;
int fd = peios_file_open(AT_FDCWD, "state.db", &p, &status);
if (fd < 0) { perror("open"); return -1; }

if (status == KACS_STATUS_CREATED) { /* we made it */ }
else                               { /* it already existed */ }
```

`status_out` tells you *what happened* — created versus opened versus overwritten — without a separate `stat` and its attendant race. If you're only ever opening existing files, use a plain open disposition and pass `sd = NULL`.

## Reading a file's security descriptor

To see who can do what to a file, read its SD. `secinfo` selects which components you want — owner, group, DACL, SACL — so you fetch only what you need:

```c
/* Probe, allocate, read (two-call). */
ssize_t need = peios_file_get_sd(AT_FDCWD, "state.db",
                                 KACS_SECINFO_OWNER | KACS_SECINFO_DACL,
                                 NULL, 0, 0);
void *sd = malloc(need);
peios_file_get_sd(AT_FDCWD, "state.db",
                  KACS_SECINFO_OWNER | KACS_SECINFO_DACL, sd, need, 0);

/* Parse it with a security.h view. */
peios_sd_view v;
peios_sd_parse(sd, need, &v);
peios_acl_view dacl;
if (peios_sd_view_dacl(&v, &dacl) == 0) {
    unsigned n = peios_acl_view_count(&dacl);
    /* iterate ACEs … */
}
free(sd);
```

If you already hold a file fd, use the fd-targeted [`peios_fd_get_sd`](~peios/sdk-files/file-h-file-security#by-fd) instead of a path — no second path resolution, and for a normal file fd the check uses the access already baked in at open.

## Changing a file's security descriptor

Writing an SD is component-selective too: name the components you're changing in `secinfo`, and everything you *don't* name is preserved. To tighten a file's DACL without touching its owner or SACL:

```c
/* Build an SD carrying only a DACL. */
peios_sd_builder *b = peios_sd_builder_new();
peios_sd_builder_dacl(b, new_acl, new_acl_len);
size_t sd_len; const void *sd_bytes = peios_sd_builder_bytes(b, &sd_len);

peios_file_set_sd(AT_FDCWD, "state.db", KACS_SECINFO_DACL, sd_bytes, sd_len, 0);
peios_sd_builder_free(b);
```

Because only `KACS_SECINFO_DACL` is selected, the owner, group, and SACL are left exactly as they were. The [`security.h` builders](~peios/sdk-security/security-h-security-descriptors#building-security-descriptors) are how you assemble the SD to apply.

## Pre-flighting an open

Sometimes you want to know whether a caller *could* open a file before you actually do. Read the file's SD, then run an [access check](~peios/sdk-access-control/checking-access) against the caller's token with `peios_file_generic_mapping` — no open, no side effects, just the verdict.

## Next

- **[`file.h` reference](~peios/sdk-files/file-h-file-security)** — every parameter, plus the fd-targeted calls and mount policy.
- **[File access](~peios/file-access/overview)** — the operator-side model of native file security.
