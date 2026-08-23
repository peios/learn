---
title: The request
description: The single struct describing every check — the core fields an ordinary check needs, and the advanced ones beneath them.
---

Every check is described by a single `struct peios_access_request`. Only the first block is needed for an ordinary check; everything below the divider is advanced and may be left zero/`NULL`. For every pointer/length pair, `NULL` is valid only when the matching length or count is zero.

```c
struct peios_access_request {
    int      token_fd;   /* -1 = the caller's effective token */
    const void *sd;      /* the object's security descriptor (wire bytes) */
    size_t   sd_len;
    uint32_t desired;    /* desired access mask */
    struct kacs_generic_mapping mapping;   /* the object class's mapping */

    /* ---- [adv] ---- */
    const void *self_sid;        /* PRINCIPAL_SELF substitution; NULL to omit */
    size_t   self_sid_len;
    uint32_t privilege_intent;   /* backup/restore intent bits */
    const struct kacs_object_type_entry *object_tree;
    uint32_t object_tree_count;
    const void *local_claims;    /* @Local claim array */
    size_t   local_claims_len;
    uint32_t pip_type;           /* 0 = use the subject's PSB */
    uint32_t pip_trust;
    const void *audit_context;   /* opaque object id for audit events */
    size_t   audit_context_len;
};
```

### The core fields

| Field | Meaning |
|---|---|
| `token_fd` | The subject token to evaluate. **`-1` means the caller's own effective token** — the common case when you are checking access for yourself. Otherwise pass a token fd from [`<peios/token.h>`](~peios/sdk-tokens/token-h-tokens-and-sessions). |
| `sd` / `sd_len` | The object's security descriptor, as self-relative wire bytes — typically from a [`peios_sd_builder`](~peios/sdk-security/security-h-security-descriptors#building-security-descriptors) or read off the object. |
| `desired` | The access mask you want checked. May contain generic bits; the `mapping` resolves them. |
| `mapping` | The object class's generic mapping (a `struct kacs_generic_mapping`), so generic rights in `desired` and in the SD's ACEs fold to the right object-specific bits. Use the class's published table — e.g. `peios_file_generic_mapping` or `peios_token_generic_mapping`. |

### The advanced fields

Leave these zero/`NULL` unless you need them:

| Field | Meaning |
|---|---|
| `self_sid` / `self_sid_len` | The SID to substitute for `PRINCIPAL_SELF` (`S-1-5-10`) in ACEs — the "self" the object belongs to. |
| `privilege_intent` | Backup/restore intent bits, letting `SeBackupPrivilege` / `SeRestorePrivilege` widen the granted mask as they would for a real backup or restore. |
| `object_tree` / `object_tree_count` | An object-type tree for a per-property check (object ACEs with type GUIDs). Mandatory for [`peios_access_check_list`](~peios/sdk-access/the-object-type-list-variant). |
| `local_claims` / `local_claims_len` | An `@Local` claim array to evaluate conditional ACEs against, beyond the claims already on the token. |
| `pip_type` / `pip_trust` | Process-integrity-protection trust label to evaluate against; `pip_type == 0` uses the subject's own PSB. |
| `audit_context` / `audit_context_len` | An opaque object identifier stamped into any audit events the check generates. |
