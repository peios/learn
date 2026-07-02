---
title: rsi/response.h — Building responses
type: reference
description: Complete reference for <rsi/response.h> — replying to RSI requests with status-only or payload-bearing responses, and the validation contract the helpers enforce.
related:
  - peios-sdk/reference/rsi-request
  - peios-sdk/reference/rsi-source
  - peios-sdk/registry-sources/building-responses
---

`<rsi/response.h>` is the sending half of a source's serve loop. After you handle a request, you reply on the source fd with a framed response. This header builds those frames for you: you pass the result as flat arrays, and librsi validates and heap-encodes the wire frame — you never hand-pack a byte.

Every response echoes the request's id and its op-code (OR'd with the response bit) and carries an `RSI_*` status. **Most operations are status-only**; five carry a payload on success. Any operation can report a *non-OK* status with the status-only helper.

For the wire, a response is a 14-byte header (echoed request id, op-code | `RSI_RESPONSE_BIT`) plus a 4-byte `RSI_*` status, followed by an op-specific payload for payload-bearing successes; multi-byte integers are little-endian and names/data are length-prefixed. You don't assemble any of that — the helpers do. Status and target-type constants (`RSI_OK`, `RSI_PATH_TARGET_GUID`, …) come from `<pkm/lcs.h>`.

## Status codes

Every response carries exactly one of these statuses. The kernel translates a non-OK status into the errno the registry client sees, so send the code that matches what actually happened:

| Code | When to send it |
|---|---|
| `RSI_OK` | The operation succeeded. Status-only ops report it via `rsi_respond_status`; the five payload-bearing ops must use their own helper. |
| `RSI_NOT_FOUND` | The requested key, entry, value, or layer does not exist in your store (client sees `ENOENT`). |
| `RSI_ALREADY_EXISTS` | A create collided with something that already exists (client sees `EEXIST`). |
| `RSI_STORAGE_ERROR` | Your backing store failed — I/O error, corruption, anything the client can't fix (client sees `EIO`). |
| `RSI_NOT_EMPTY` | The operation needs the key to have no children, and it has some (client sees `ENOTEMPTY`). |
| `RSI_TOO_LARGE` | The data exceeds what the source is willing or able to store (client sees `ENOSPC`). |
| `RSI_TXN_BUSY` | A transaction can't proceed right now — e.g. write-lock contention; the operation may be retried (client sees `EBUSY`). |
| `RSI_INVALID` | The request is well-formed RSI but violates the source's rules or refers to something malformed (client sees `EINVAL`). |
| `RSI_CAS_FAILED` | A sequence-guarded write's `expected_sequence` did not match the current entry — the compare-and-swap lost (client sees `EAGAIN` and retries). |
| `RSI_TXN_NOT_SUPPORTED` | Reply to `BEGIN_TRANSACTION` from a source that does not implement transactions (client sees `ENOTSUP`). |

## The response contract

All `rsi_respond_*` helpers return `0`, or `-1` with `errno`. A set of rules applies to **every** helper, and violating one is an `EINVAL` caller-contract error:

- **`(ptr, len)` pairs:** a pointer may be `NULL` only when its length/count is zero.
- **Boolean fields** (`volatile_key`, `symlink`, target types) must be exactly `0` or `1`.
- **Hidden path targets** (`RSI_PATH_TARGET_HIDDEN`) must carry an **all-zero** `target_guid`.
- **`LOOKUP`/`ENUM_CHILDREN` metadata** must exactly cover the GUID path targets referenced — no missing metadata, no duplicates, no unreferenced entries.
- **`DELETE_LAYER` orphan GUIDs** must be nonzero and unique.

Beyond `EINVAL`, any helper can also fail with `ENOMEM` (during validation or frame allocation), `EOVERFLOW` (validation arithmetic or the assembled frame too large), `EIO` (a short `write`), or the raw `write(2)` errno. Per-helper `EINVAL` additions are noted below.

## Sending a pre-built frame

```c
ssize_t rsi_write_response(int fd, const void *frame, size_t len);
```

Writes one already-built response frame to the source fd — a thin `write(2)` wrapper returning the bytes written, or `-1` with `errno`. Most callers never need this; the `rsi_respond_*` helpers build *and* send. It exists for callers assembling frames by other means.

## Status-only responses

```c
int rsi_respond_status(int fd, const struct rsi_request *req, uint32_t status);
```

The workhorse. Use it for:

- **status-only ops on success** — pass `status = RSI_OK`; and
- **any op reporting a non-OK status** — a `LOOKUP` that found nothing, a `SET_VALUE` that failed a compare-and-swap, a permission error: reply with the appropriate `RSI_*` status here, whatever the op.

It fails with `EINVAL` on a bad `req`, an unknown `status`, or `RSI_OK` given for a payload-bearing op (those must use their own helper on success), plus `EIO` / the `write` error.

The rule of thumb: **on failure, always `rsi_respond_status`; on success, `rsi_respond_status` unless the op is one of the five below.**

## Payload-bearing responses

Five operations return data on success. Each takes the result as flat arrays and encodes the frame for you.

### LOOKUP

```c
struct rsi_path_entry {
    const void *layer;  uint32_t layer_len;
    uint8_t     target_type;   /* RSI_PATH_TARGET_GUID (0) / RSI_PATH_TARGET_HIDDEN (1) */
    uint8_t     target_guid[16];
    uint64_t    sequence;
};
struct rsi_key_metadata {
    uint8_t     guid[16];
    const void *sd;  uint32_t sd_len;
    uint8_t     volatile_key;
    uint8_t     symlink;
    uint64_t    last_write_time;
};

int rsi_respond_lookup(int fd, const struct rsi_request *req,
                       const struct rsi_path_entry *entries, uint32_t entry_count,
                       const struct rsi_key_metadata *metadata, uint32_t metadata_count);
```

Answers a `LOOKUP` with the resolved path `entries` for the child — one per layer that has a view of it, each either a **GUID** target or a **HIDDEN** (tombstone) target — plus the `metadata` for every key the entries reference. A `RSI_PATH_TARGET_HIDDEN` entry must carry an all-zero `target_guid`; the metadata must exactly cover the GUID targets. `EINVAL` if `req` is not a `LOOKUP`, a nonzero count has a NULL array, or an entry has invalid target/boolean fields, missing/duplicate metadata, or unreferenced metadata.

### ENUM_CHILDREN

```c
struct rsi_child_entry {
    const void            *child_name;  uint32_t child_name_len;
    const struct rsi_path_entry *entries;  uint32_t entry_count;
};

int rsi_respond_enum_children(int fd, const struct rsi_request *req,
                              const struct rsi_child_entry *children, uint32_t child_count,
                              const struct rsi_key_metadata *metadata, uint32_t metadata_count);
```

Answers an `ENUM_CHILDREN` with each `child` — its name and the [path entries](#lookup) that resolve it — plus the `metadata` for every referenced key. The same target/boolean/metadata-coverage rules as `LOOKUP` apply. `EINVAL` on the same conditions, scoped to `ENUM_CHILDREN`.

### READ_KEY

```c
int rsi_respond_read_key(int fd, const struct rsi_request *req, const void *name,
                         uint32_t name_len, const uint8_t *parent_guid, const void *sd,
                         uint32_t sd_len, uint8_t volatile_key, uint8_t symlink,
                         uint64_t last_write_time);
```

Answers a `READ_KEY` with the key's non-layered metadata: its `name`, `parent_guid`, security descriptor (`sd`), the `volatile_key`/`symlink` flags, and `last_write_time`. `EINVAL` if `req` is not a `READ_KEY`, `parent_guid` is NULL, or a boolean field is invalid.

### QUERY_VALUES

```c
struct rsi_value_entry {
    const void *value_name;  uint32_t value_name_len;
    const void *layer_name;  uint32_t layer_name_len;
    uint32_t    value_type;
    const void *data;  uint32_t data_len;
    uint64_t    sequence;
};
struct rsi_blanket_entry {
    const void *layer_name;  uint32_t layer_name_len;
    uint64_t    sequence;
};

int rsi_respond_query_values(int fd, const struct rsi_request *req,
                             const struct rsi_value_entry *entries, uint32_t entry_count,
                             const struct rsi_blanket_entry *blankets, uint32_t blanket_count);
```

Answers a `QUERY_VALUES` with the value `entries` — each value's name, the layer it lives in, its type, data, and sequence — plus the `blankets` (the blanket tombstones on this key, each a layer and sequence). The kernel resolves precedence across the layers you report. `EINVAL` if `req` is not a `QUERY_VALUES` or a nonzero count has a NULL array.

### DELETE_LAYER

```c
int rsi_respond_delete_layer(int fd, const struct rsi_request *req,
                             const uint8_t *orphaned_guids, uint32_t orphaned_count);
```

Answers a `DELETE_LAYER` with the GUIDs of the keys the deleted layer orphaned — a flat `orphaned_count * 16`-byte array. The GUIDs must be nonzero and unique. `EINVAL` if `req` is not a `DELETE_LAYER` or a nonzero count has a NULL array, a nil GUID, or a duplicate.

## The five at a glance

| Success response | Op | Payload |
|---|---|---|
| `rsi_respond_lookup` | `LOOKUP` | path entries + referenced key metadata |
| `rsi_respond_enum_children` | `ENUM_CHILDREN` | children (name + path entries) + metadata |
| `rsi_respond_read_key` | `READ_KEY` | one key's non-layered metadata |
| `rsi_respond_query_values` | `QUERY_VALUES` | value entries + blanket tombstones |
| `rsi_respond_delete_layer` | `DELETE_LAYER` | orphaned key GUIDs |

Every other op — and every failure of these — is `rsi_respond_status`.

## See also

- **[`<rsi/request.h>`](~peios-sdk/reference/rsi-request)** — decoding the request each of these replies to.
- **[Building responses](~peios-sdk/registry-sources/building-responses)** — choosing and filling the right responder.
