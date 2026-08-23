---
title: Mount policy
description: How KACS treats a superblock that cannot store native descriptors, and the entry points for reading and setting that policy.
---

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
