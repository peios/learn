---
title: Logon sessions
description: The lightweight kernel bookkeeping a token references, and the entry points for creating and destroying one.
---

A **logon session** is the lightweight kernel bookkeeping a token references — the "login" a token belongs to. Creating and destroying them requires `SeTcbPrivilege`.

```c
struct peios_session_spec {
    uint8_t     logon_type;     /* KACS_LOGON_TYPE_* */
    const char *auth_package;   /* UTF-8; may be "" */
    const void *user_sid;
    size_t      user_sid_len;
};

int peios_session_create(const struct peios_session_spec *spec, uint64_t *id_out);
int peios_session_destroy_empty(uint64_t session_id);
```

- `peios_session_create` creates a logon session of type `logon_type` (`KACS_LOGON_TYPE_*` — interactive, network, service, …) for `user_sid`, attributing it to `auth_package`. `id_out` is mandatory and receives the new session id, which you then pass to `peios_token_builder_session`. Errors: `EPERM` (`SeTcbPrivilege` missing), `EINVAL` (`NULL` spec, `id_out`, or field; malformed SID; oversized spec), `EFAULT` (bad pointer), `ENOMEM` (allocation failed).
- `peios_session_destroy_empty` destroys a session that has **no live tokens** — it fails rather than orphaning tokens. Clean up sessions only after every token referencing them is closed. Errors: `EPERM` (`SeTcbPrivilege` missing), `ENOENT` (no such session), `EBUSY` (live tokens, linked-pair state, or in-flight references).
