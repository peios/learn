---
title: Syscalls
description: The three LCS syscalls — reg_open_key, reg_create_key and reg_begin_transaction — with their arguments and failure conditions.
---

## `reg_open_key` (1100)

```c
int reg_open_key(int parent_fd, const char __user *path,
                 u32 desired_access, u32 flags);
```

Opens an existing key. Fails if it does not exist after layer
resolution.

| Parameter | Description |
|---|---|
| `parent_fd` | An open key fd to resolve relative to, or -1 for an absolute path. No AccessCheck is performed on the parent. |
| `path` | A null-terminated registry path — absolute with a hive prefix when `parent_fd` is -1, relative to the parent key otherwise. |
| `desired_access` | Requested rights, raw generic bits, `MAXIMUM_ALLOWED`, or a combination (§5.4.2). Zero and unknown bits are `EINVAL`. |
| `flags` | `REG_OPEN_LINK` (`0x01`) opens a symlink key rather than following it. Every other bit is reserved and must be zero. |

The open proceeds as follows.

1. Parse and canonicalise the path: normalise separators, reject empty
   components and a trailing separator, check the total length and each
   component length.
2. Rewrite a leading `CurrentUser\` to `Users\<caller SID>\` — only for
   an absolute path, and only the first component (§5.2.1).
3. Route. For an absolute path, look the hive name up, private hives
   before global ones. For a relative one, use the parent key's source
   and resolve from the parent's GUID.
4. Walk the path component by component through `RSI_LOOKUP`, resolving
   each through the layer stack and following symlinks — except a final
   component when `REG_OPEN_LINK` is set. Collect the ancestor chain as
   you go.
5. Run AccessCheck against the final key's descriptor.
6. Publish an fd holding the key GUID, the granted mask, the resolved
   path and the ancestor chain.

If the path traversed a symlink, the fd stores the *resolved* path and
ancestor chain. It refers to the target object.

| Errno | Condition |
|---|---|
| `ENOENT` | The key does not exist after layer resolution. |
| `EACCES` | AccessCheck did not grant everything requested. |
| `EINVAL` | Malformed path; zero or unknown `desired_access` bits; a symlink whose effective default value is not `REG_LINK`; maximum depth exceeded. |
| `ELOOP` | Symlink depth limit exceeded. |
| `ENAMETOOLONG` | A component or the total path is too long. |
| `ETIMEDOUT` | The source did not answer within `RequestTimeoutMs`. |
| `EIO` | The source failed or is unavailable. |
| `ENOMEM` | Kernel allocation failure. |

## `reg_create_key` (1101)

```c
int reg_create_key(const struct reg_create_key_args __user *args);
```

Opens the key if it exists after layer resolution, creates it with an
inherited descriptor if not, and reports which happened.

| Field | Description |
|---|---|
| `parent_fd` | As `reg_open_key`. |
| `path_ptr` | Pointer to a null-terminated path. |
| `desired_access` | As `reg_open_key`. |
| `flags` | `REG_OPTION_VOLATILE` (`0x01`), `REG_OPTION_CREATE_LINK` (`0x02`). Other bits reserved. |
| `layer_ptr` | Pointer to a null-terminated layer name for creation, or null for the base layer. Ignored if the key already exists. |
| `txn_fd` | A transaction fd, or -1. A non-negative value makes creation a mutating operation that binds or reuses that transaction. |
| `disposition_ptr` | Receives `REG_CREATED_NEW` (1) or `REG_OPENED_EXISTING` (2). May be null. |
| `_pad0`, `_pad1` | Reserved; must be zero. |

**If the key exists**, this behaves as `reg_open_key`, the layer
parameter is ignored, and the disposition is `REG_OPENED_EXISTING`.

**If it does not:**

1. Resolve the parent, which must exist. Check that the parent's depth
   plus one is within `MaxKeyDepth`.
2. AccessCheck the parent for `KEY_CREATE_SUB_KEY`.
3. Perform layer write authorization against the target layer's
   metadata key (§5.3.4).
4. Mint a fresh UUIDv4 GUID.
5. Compute the new key's descriptor from the parent's, through KACS.
6. Create the path entry with a new sequence number, then the key
   record (§5.2.5).
7. AccessCheck the *new* key's inherited descriptor against
   `desired_access` — an inherited descriptor may not grant everything
   the creator asked for.
8. Publish the fd with the granted mask and disposition
   `REG_CREATED_NEW`.

Intermediate path components are not auto-created. Only the final one
is.

**Races.** If two callers race, one creates and the other observes the
key as existing. `RSI_ALREADY_EXISTS` on the path entry is retried as
an open, reporting `REG_OPENED_EXISTING`, and `EEXIST` never reaches
userspace from this syscall. `RSI_ALREADY_EXISTS` on the *key record*,
for a GUID LCS has just minted, is not a race — the source and the
kernel disagree about what exists — and fails closed with `EIO`
(§5.2.3).

| Errno | Condition, in addition to `reg_open_key`'s |
|---|---|
| `ENOENT` | The parent does not exist, or the named layer is not in the layer table. |
| `EACCES` | The parent denied `KEY_CREATE_SUB_KEY`, the inherited descriptor denied the requested access, or layer write authorization failed. |
| `EPERM` | `REG_OPTION_CREATE_LINK` without `KEY_CREATE_LINK` on the parent, or without `SeTcbPrivilege` or Administrators. |
| `ENOSPC` | The per-value layer cap was exceeded. |
| `EINVAL` | A non-volatile key under a volatile parent; a non-zero reserved field. |

## `reg_begin_transaction` (1102)

```c
int reg_begin_transaction(void);
```

Allocates a transaction id, publishes a transaction fd in state
`REG_TXN_ACTIVE_UNBOUND`, and starts the lifetime timer. It contacts no
source and chooses none (§5.7.1). It can fail only with `ENOMEM`,
`EOVERFLOW` on transaction id exhaustion, or `EINVAL`.
