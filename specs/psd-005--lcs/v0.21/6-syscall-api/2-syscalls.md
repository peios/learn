---
title: Syscalls
---

LCS defines three syscalls, numbered in the PKM range starting at
1100.

## reg_open_key (1100)

Open an existing registry key. Fails if the key does not exist
after layer resolution.

```
int reg_open_key(int parent_fd, const char *path,
                 uint32_t desired_access, uint32_t flags);
```

### Parameters

| Parameter | Description |
|---|---|
| parent_fd | An open key fd to use as the root for relative path resolution, or -1 for absolute path resolution. If provided, path is resolved relative to this key. No AccessCheck is performed on the parent -- the caller already proved access when they obtained the parent fd. |
| path | Null-terminated registry path. If parent_fd is -1, this is an absolute path with hive prefix. If parent_fd is a valid key fd, this is a relative path from that key. Backslash or forward-slash separated -- forward slashes normalised to backslashes. `CurrentUser\` is rewritten to `Users\<caller SID>\` only when it appears as the first component of an absolute path (parent_fd is -1). |
| desired_access | Bitmask of requested access rights (§3.1), or MAXIMUM_ALLOWED. All requested rights MUST be granted or the open fails. |
| flags | Bitfield. REG_OPEN_LINK (0x01): open the symlink key itself rather than following it. All other bits reserved, MUST be zero. |

### Returns

Key fd on success. -1 with errno on failure.

### Behaviour

1. Parse and canonicalise the path. Normalise forward slashes,
   validate structure (no empty components, no trailing separator).
   Validate total path length against MaxTotalPathLength. Validate
   each component against MaxPathComponentLength.
2. Rewrite `CurrentUser\` to `Users\<caller SID>\` if the first
   component is `CurrentUser`. This rewriting applies only to the
   caller-supplied path, not to symlink targets encountered during
   resolution.
3. Route to the source. If parent_fd is -1, extract the first
   path component (hive name) and look it up in the routing table
   (private hives first, then global hives — private hives can
   shadow global hives). If parent_fd is a valid key fd, the
   source is the same source that backs the parent key's hive.
   The path is resolved relative to the parent key's GUID.
4. Walk the path component by component via RSI Lookup operations.
   At each component, resolve through the layer stack to find the
   effective key. Follow symlinks (unless the final component is a
   symlink and REG_OPEN_LINK is set). Collect the ancestor chain
   (GUID at each component).
5. Evaluate AccessCheck against the final key's SD with the
   caller's token and desired_access.
6. Create an anonymous fd storing the key GUID, granted access
   mask, resolved path, and ancestor chain. Return the fd.

### Symlink path identity

If the path traversed a symlink, the fd stores the resolved path
and ancestor chain (actual GUIDs after following the symlink), not
the original symlink path. The fd refers to the target object.

To operate on the symlink key itself, open with REG_OPEN_LINK.

### Errors

| Errno | Condition |
|---|---|
| ENOENT | Key does not exist after layer resolution. |
| EACCES | AccessCheck did not grant all requested access rights. |
| EINVAL | Invalid path (empty components, null, malformed). Symlink target is not REG_LINK type. Maximum key depth exceeded. |
| ELOOP | Symlink depth limit exceeded during path walk. |
| ETIMEDOUT | Source did not respond within RequestTimeoutMs. |
| EIO | Source returned an internal error or is unavailable. |
| ENOMEM | Kernel memory allocation failed. |
| ENAMETOOLONG | Key name component exceeds MaxPathComponentLength, or total path length exceeds MaxTotalPathLength. |

## reg_create_key (1101)

Open or create a registry key. If the key exists after layer
resolution, opens it. If not, creates it with an inherited SD.
Returns a disposition indicating which occurred.

```
int reg_create_key(int parent_fd, const char *path,
                   uint32_t desired_access, const char *layer,
                   uint32_t flags, uint32_t *disposition);
```

### Parameters

| Parameter | Description |
|---|---|
| parent_fd | As reg_open_key. |
| path | As reg_open_key. |
| desired_access | As reg_open_key. |
| layer | Null-terminated layer name for key creation. If null, the base layer is used. Ignored if the key already exists. |
| flags | Bitfield. REG_OPTION_VOLATILE (0x01): create a volatile key. REG_OPTION_CREATE_LINK (0x02): create a symlink key. All other bits reserved. |
| disposition | Output pointer. Set to REG_CREATED_NEW (1) if created, or REG_OPENED_EXISTING (2) if the key already existed. MAY be null. |

### Returns

Key fd on success. -1 with errno on failure.

### Behaviour (key exists)

Same as reg_open_key. The layer parameter is ignored. Disposition
is set to REG_OPENED_EXISTING.

**Race handling.** If two concurrent reg_create_key calls race on
the same path, one creates the key and the other observes it as
existing. If RSI_CREATE_ENTRY returns RSI_ALREADY_EXISTS, LCS
retries as an open (disposition REG_OPENED_EXISTING). EEXIST is
never returned to userspace from reg_create_key.

### Behaviour (key does not exist)

1. Resolve the parent path. The parent MUST exist. Validate that
   the parent's depth + 1 does not exceed MaxKeyDepth.
2. Evaluate AccessCheck on the parent key with KEY_CREATE_SUB_KEY.
3. Perform layer write authorization: verify the caller's token
   has KEY_SET_VALUE on the target layer's metadata key at
   `Machine\System\Registry\Layers\<layer>\`. If layer is null
   (base layer), check against the base layer's metadata key. If
   the base layer's metadata key does not yet exist (first boot
   before seed restore), LCS uses the compiled-in default SD
   (SYSTEM and Administrators: KEY_ALL_ACCESS).
4. Assign a new GUID.
5. Compute the new key's SD from the parent's SD via the KACS
   inheritance algorithm (PSD-004 §3.6).
6. Create a path entry (parent, name, layer) → GUID with a new
   sequence number via RSI.
7. Create the key record (GUID, name, parent GUID, SD, flags) via
   RSI.
8. Evaluate AccessCheck on the new key's SD with desired_access.
   The inherited SD may not grant everything requested.
9. Create the fd with granted access. Set disposition to
   REG_CREATED_NEW. Return the fd.

### Additional errors

| Errno | Condition |
|---|---|
| ENOENT | Parent key does not exist. Target layer does not exist in layer table. |
| EACCES | Parent denied KEY_CREATE_SUB_KEY, new key's inherited SD denied requested access, or layer write authorization failed. |
| ENOSPC | Layer cap exceeded for this path. |
| EINVAL | Non-volatile key under volatile parent. Maximum key depth exceeded. |
| EPERM | REG_OPTION_CREATE_LINK without SeTcbPrivilege or Administrator membership. |
| ENAMETOOLONG | Key name component exceeds MaxPathComponentLength, or total path length exceeds MaxTotalPathLength. |
| ETIMEDOUT | Source did not respond within RequestTimeoutMs. |
| EIO | Source returned an internal error or is unavailable. |

### Notes

- Creating a volatile key under a non-volatile parent is permitted.
  Creating a non-volatile key under a volatile parent is forbidden
  (EINVAL).
- REG_OPTION_CREATE_LINK requires KEY_CREATE_LINK on the parent
  and SeTcbPrivilege or Administrator group membership.
- Intermediate path components are NOT auto-created. Only the final
  component is created.

## reg_begin_transaction (1102)

Begin a new registry transaction. Returns a transaction fd.

```
int reg_begin_transaction(void);
```

### Parameters

None.

### Returns

Transaction fd on success. -1 with errno on failure.

### Behaviour

1. Allocate a transaction ID (kernel-internal, monotonic).
2. Create an anonymous fd storing the transaction ID. Source
   binding is deferred until the first operation.
3. Start the transaction timeout timer.
4. Return the fd.

### Errors

| Errno | Condition |
|---|---|
| ENOMEM | Kernel memory allocation failed. |
| ENOTSUP | Source does not support explicit transactions. |
