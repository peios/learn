---
title: access.h — Access checks
type: reference
description: Complete reference for <peios/access.h> — running the KACS AccessCheck pipeline for a token against a security descriptor, including the object-type-list variant.
related:
  - peios-sdk/reference/security
  - peios-sdk/reference/token
  - peios/access-decisions/overview
---

`<peios/access.h>` answers the central question of the whole access-control model: *may this subject perform this access on this object?* You hand it a token, a security descriptor, and a desired access mask, and it runs the full KACS AccessCheck pipeline and tells you whether access is granted and exactly which rights were granted.

Two things are worth saying up front:

- **These calls are advisory.** They *evaluate*, they do not *enforce*. `peios_access_check` tells you what the answer would be; enforcement of a real operation always runs inside the kernel against the subject's own process security block. Use these when *your* code is the resource manager — you hold an object, you have its security descriptor, and you need to make the grant/deny decision yourself.
- **A denial is a normal result, not an error.** Per the [library conventions](~peios-sdk/getting-started/library-conventions#structured-results-out-parameters), a denied check returns `-1` with `errno == EACCES`, and the granted mask is still written out. Only a genuine failure (a bad token fd, a malformed SD) is an error in the usual sense.

## The request

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
| `token_fd` | The subject token to evaluate. **`-1` means the caller's own effective token** — the common case when you are checking access for yourself. Otherwise pass a token fd from [`<peios/token.h>`](~peios-sdk/reference/token). |
| `sd` / `sd_len` | The object's security descriptor, as self-relative wire bytes — typically from a [`peios_sd_builder`](~peios-sdk/reference/security#building-security-descriptors) or read off the object. |
| `desired` | The access mask you want checked. May contain generic bits; the `mapping` resolves them. |
| `mapping` | The object class's generic mapping (a `struct kacs_generic_mapping`), so generic rights in `desired` and in the SD's ACEs fold to the right object-specific bits. Use the class's published table — e.g. `peios_file_generic_mapping` or `peios_token_generic_mapping`. |

### The advanced fields

Leave these zero/`NULL` unless you need them:

| Field | Meaning |
|---|---|
| `self_sid` / `self_sid_len` | The SID to substitute for `PRINCIPAL_SELF` (`S-1-5-10`) in ACEs — the "self" the object belongs to. |
| `privilege_intent` | Backup/restore intent bits, letting `SeBackupPrivilege` / `SeRestorePrivilege` widen the granted mask as they would for a real backup or restore. |
| `object_tree` / `object_tree_count` | An object-type tree for a per-property check (object ACEs with type GUIDs). Mandatory for [`peios_access_check_list`](#the-object-type-list-variant). |
| `local_claims` / `local_claims_len` | An `@Local` claim array to evaluate conditional ACEs against, beyond the claims already on the token. |
| `pip_type` / `pip_trust` | Process-integrity-protection trust label to evaluate against; `pip_type == 0` uses the subject's own PSB. |
| `audit_context` / `audit_context_len` | An opaque object identifier stamped into any audit events the check generates. |

## The check

```c
int peios_access_check(const struct peios_access_request *req,
                       uint32_t *granted, struct peios_access_audit *audit);
```

Runs the full AccessCheck pipeline. Returns:

- **`0`** if *every* right in `desired` is granted;
- **`-1` with `errno == EACCES`** if any desired right is denied;
- **`-1` with another errno** on a real error (e.g. `EBADF` for a bad `token_fd`, `EINVAL` for a malformed SD).

`granted`, if non-`NULL`, **always** receives the granted access mask — even on denial. This is the useful part: you can request a broad `desired` and read back exactly which subset was granted, rather than probing one right at a time. `audit`, if non-`NULL`, receives the [audit outputs](#audit-outputs).

```c
struct peios_access_request req = {
    .token_fd = -1,                      /* my own effective token */
    .sd = sd_bytes, .sd_len = sd_len,
    .desired = KACS_ACCESS_READ | KACS_ACCESS_WRITE,
    .mapping = peios_file_generic_mapping,
};

uint32_t granted = 0;
int rc = peios_access_check(&req, &granted, NULL);
if (rc == 0) {
    /* both READ and WRITE granted */
} else if (errno == EACCES) {
    /* denied; `granted` shows what WAS allowed (maybe READ only) */
} else {
    /* error: perror("access_check") */
}
```

libpeios owns the versioned `struct kacs_access_check_args` under the hood — it sets `caller_size` and zeroes the reserved fields so the request stays forward-compatible across kernel versions. You only ever fill in the `peios_access_request` above.

## Audit outputs

```c
struct peios_access_audit {
    uint32_t continuous_audit;   /* OR of matching alarm masks */
    int      staging_mismatch;   /* 1 if the staged CAAP result differs */
};
```

When you pass a non-`NULL` `audit`, the check reports:

- `continuous_audit` — the OR of the alarm masks of any `SYSTEM_AUDIT` ACEs that matched, i.e. what a continuous-audit consumer would log for this access.
- `staging_mismatch` — `1` if evaluating the *staged* central access policy would have produced a different result than the active one. This is the signal you watch when rolling out a [central access policy](~peios/central-access-policies/overview) change: a non-zero value means the pending policy would decide this access differently.

## The object-type-list variant

```c
int peios_access_check_list(const struct peios_access_request *req,
                            struct kacs_node_result *results, uint32_t count);
```

`peios_access_check_list` is the `AccessCheckByTypeResultList` form — a *per-node* check over an object-type tree, for objects whose properties or property sets carry their own object ACEs (a directory-service-style object, say). It evaluates the whole tree in one call and reports a separate result for each node.

- `req->object_tree` / `object_tree_count` are **mandatory** here — they describe the tree of `kacs_object_type_entry` nodes to evaluate.
- `results` receives **one `kacs_node_result` per node, in preorder**, and `count` **must equal** `req->object_tree_count`.
- Returns `0` / `-1` (`EINVAL` if `count` doesn't match, and the usual errors otherwise).

Each `kacs_node_result` carries that node's granted mask and status, so you can discover, for example, that a caller may read most of an object but not one protected property — in a single check rather than one per property.

## See also

- **[`<peios/security.h>`](~peios-sdk/reference/security)** — building the security descriptors and reading the generic-mapping tables this check consumes.
- **[`<peios/token.h>`](~peios-sdk/reference/token)** — obtaining the `token_fd` to check, and `peios_token_generic_mapping`.
- **[Access decisions](~peios/access-decisions/overview)** — the operator-side account of how KACS reaches a grant/deny decision.
