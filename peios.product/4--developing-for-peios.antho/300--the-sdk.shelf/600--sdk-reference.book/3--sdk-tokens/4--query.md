---
title: Query
description: Reading a token's contents by information class — the generic reader, and the typed wrappers over the common classes.
---

You read a token's contents by **information class**. The generic reader handles any class getxattr-style; typed convenience wrappers cover the common ones.

```c
ssize_t peios_token_query(int fd, uint32_t info_class, void *buf, size_t cap);
ssize_t peios_token_user(int fd, void *sid_buf, size_t cap);   /* CLASS_USER */
```

- `peios_token_query` reads the class `info_class` (`KACS_TOKEN_CLASS_*`) into `buf` using the [two-call protocol](~peios/sdk-conventions/library-conventions#the-two-call-buffer-protocol). Classes that return SID arrays or ACLs are parsed afterward with the [`<peios/security.h>` views](~peios/sdk-security/security-h-security-descriptors#parsing-views) — e.g. read `CLASS_GROUPS` into a buffer, then `peios_sid_array_parse` it.
- `peios_token_user` is the same two-call read specialised to the user SID (`CLASS_USER`): probe with `sid_buf == NULL, cap == 0`, then retrieve.

For the common scalar classes there are typed helpers that write through a mandatory non-`NULL` out-pointer and return `0` / `-1`:

```c
struct peios_privilege_set {
    uint64_t present;
    uint64_t enabled;
    uint64_t enabled_by_default;
    uint64_t used;
};

int peios_token_type(int fd, uint32_t *out);            /* CLASS_TYPE */
int peios_token_session_id(int fd, uint32_t *out);      /* CLASS_SESSION_ID */
int peios_token_integrity(int fd, uint32_t *level_rid_out); /* CLASS_INTEGRITY_LEVEL */
int peios_token_privileges(int fd, struct peios_privilege_set *out); /* CLASS_PRIVILEGES */
```

`peios_token_privileges` returns all four privilege words at once: which privileges are `present`, which are `enabled`, which are `enabled_by_default`, and which have been `used` (the audit trail of privilege use).

Errors (all query calls): `EACCES` (handle lacks `QUERY`), `EINVAL` (unknown class), `ERANGE` (non-probe buffer too small), `EFAULT` (bad buffer pointer). The typed helpers add `EINVAL` (`NULL` out-pointer, or an unexpected payload shape).
