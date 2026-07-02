---
title: rsi/request.h — Decoding requests
type: reference
description: Complete reference for <rsi/request.h> — reading framed RSI requests from the source fd, splitting header from payload, and decoding each operation's payload with its typed parser.
related:
  - peios-sdk/reference/rsi-source
  - peios-sdk/reference/rsi-response
  - peios-sdk/registry-sources/serving-requests
---

`<rsi/request.h>` is the receiving half of a registry source's serve loop. The kernel sends your source [RSI](~peios-sdk/registry-sources/overview) requests — "look up this child", "store this value", "begin this transaction" — as framed messages on the source fd. This header reads one frame, splits its header from its payload, and decodes the payload into a flat, typed struct you can act on.

The shape of the loop is always: **read a frame → parse the header → dispatch on the op-code → decode the payload with the matching parser**. The decoders are thin wrappers over the kernel's own RSI parsers, so your wire handling is guaranteed compatible with what the kernel sent.

> **Borrowing:** every decoded name/data field is a `(ptr, len)` pair that **borrows into your frame buffer**. The pointers are valid only until you reuse that buffer for the next `rsi_read_request`. Copy out anything you need to keep across iterations. This is the same [borrow discipline](~peios-sdk/getting-started/library-conventions#memory-ownership) as libpeios's views.

Op-code and field constants (`RSI_LOOKUP`, `RSI_WRITE_KEY_FIELD_*`, `RSI_TXN_*`) come from `<pkm/lcs.h>`.

## Reading and parsing a frame

```c
struct rsi_request {
    uint64_t    request_id;   /* echo this in the response */
    uint64_t    txn_id;       /* transaction id (0 outside a transaction) */
    const void *payload;      /* borrowed; valid until the frame is reused */
    uint32_t    payload_len;
    uint16_t    op_code;      /* RSI_LOOKUP, RSI_SET_VALUE, … — dispatch on this */
};

ssize_t rsi_read_request(int fd, void *buf, size_t cap);
int     rsi_parse_request(const void *frame, size_t len, struct rsi_request *out);
```

- **`rsi_read_request`** reads one framed request from the source fd into `buf` — a thin `read(2)` wrapper that **blocks** until a request is queued, then returns the frame length (pass it to `rsi_parse_request`). It returns **`0` at EOF** (the source is closing — leave the loop) or `-1` with `errno`, notably **`EMSGSIZE`** if `cap` is smaller than the pending frame (size `buf` generously, or grow and retry).
- **`rsi_parse_request`** splits a frame into its header and payload view, filling `out` with the `request_id` (which you must echo in the response), the `txn_id` (`0` when the request is not inside a transaction), the `op_code` to dispatch on, and a **borrowed** `payload` pointer. Returns `0`, or `-1` with `errno` (`EINVAL` on NULL args, `EBADMSG` on a malformed frame).

## The decoders

Each decoder takes the parsed `req` and fills a flat struct: GUIDs by value, names and data as borrowed `(ptr, len)` pairs. All return `0`, or `-1` with `errno` — **`EINVAL`** if the arguments are NULL *or the decoder doesn't match `req->op_code`* (so calling the wrong decoder for an op is a clean error), and **`EBADMSG`** on a malformed payload. You dispatch on `req.op_code` and call the matching one.

### Path and entry operations

These operate on the name→GUID bindings that make up the key hierarchy. A *child* is named under a *parent* GUID, and entries live in *layers*.

```c
/* LOOKUP — is child_name visible under parent_guid? */
struct rsi_lookup {
    uint8_t     parent_guid[16];
    const void *child_name;  uint32_t child_name_len;
};
int rsi_request_lookup(const struct rsi_request *req, struct rsi_lookup *out);

/* CREATE_ENTRY — bind child_name → child_guid in layer_name. */
struct rsi_create_entry {
    uint8_t     parent_guid[16];
    uint8_t     child_guid[16];
    const void *child_name;  uint32_t child_name_len;
    const void *layer_name;  uint32_t layer_name_len;
    uint64_t    sequence;
};
int rsi_request_create_entry(const struct rsi_request *req, struct rsi_create_entry *out);

/* HIDE_ENTRY — tombstone child_name in layer_name. */
struct rsi_hide_entry {
    uint8_t     parent_guid[16];
    const void *child_name;  uint32_t child_name_len;
    const void *layer_name;  uint32_t layer_name_len;
    uint64_t    sequence;
};
int rsi_request_hide_entry(const struct rsi_request *req, struct rsi_hide_entry *out);

/* DELETE_ENTRY — remove child_name's entry in layer_name. */
struct rsi_delete_entry {
    uint8_t     parent_guid[16];
    const void *child_name;  uint32_t child_name_len;
    const void *layer_name;  uint32_t layer_name_len;
};
int rsi_request_delete_entry(const struct rsi_request *req, struct rsi_delete_entry *out);

/* ENUM_CHILDREN — list the children of parent_guid. */
struct rsi_enum_children { uint8_t parent_guid[16]; };
int rsi_request_enum_children(const struct rsi_request *req, struct rsi_enum_children *out);
```

| Op | You must | Reply with |
|---|---|---|
| `LOOKUP` | Resolve `child_name` under `parent_guid` across your layers. | [`rsi_respond_lookup`](~peios-sdk/reference/rsi-response#lookup) |
| `CREATE_ENTRY` | Bind `child_name` → `child_guid` in `layer_name` at `sequence`. | status |
| `HIDE_ENTRY` | Place a tombstone for `child_name` in `layer_name`. | status |
| `DELETE_ENTRY` | Remove `child_name`'s entry in `layer_name`. | status |
| `ENUM_CHILDREN` | List every child of `parent_guid`. | [`rsi_respond_enum_children`](~peios-sdk/reference/rsi-response#enum_children) |

### Key operations

These operate on key *metadata* records — the non-layered facts about a key (its name, parent, security descriptor, flags).

```c
/* CREATE_KEY — create the metadata record guid under parent_guid. */
struct rsi_create_key {
    uint8_t     guid[16];
    uint8_t     parent_guid[16];
    const void *name;  uint32_t name_len;
    const void *sd;    uint32_t sd_len;
    uint8_t     volatile_key;  /* 1 if volatile */
    uint8_t     symlink;       /* 1 if a symlink */
};
int rsi_request_create_key(const struct rsi_request *req, struct rsi_create_key *out);

/* READ_KEY / DROP_KEY — a request carrying just a key GUID. */
struct rsi_key_guid { uint8_t guid[16]; };
int rsi_request_read_key(const struct rsi_request *req, struct rsi_key_guid *out);
int rsi_request_drop_key(const struct rsi_request *req, struct rsi_key_guid *out);

/* WRITE_KEY — update the mutable fields of guid named by field_mask. */
struct rsi_write_key {
    uint8_t     guid[16];
    uint32_t    field_mask;        /* RSI_WRITE_KEY_FIELD_SD | …_LAST_WRITE_TIME */
    const void *sd;  uint32_t sd_len;/* NULL when the SD bit is clear */
    uint64_t    last_write_time;   /* valid only when the time bit is set */
};
int rsi_request_write_key(const struct rsi_request *req, struct rsi_write_key *out);
```

| Op | You must | Reply with |
|---|---|---|
| `CREATE_KEY` | Store the metadata record for `guid` (its name, parent, `sd`, and the `volatile_key`/`symlink` flags). | status |
| `READ_KEY` | Return the metadata of `guid`. | [`rsi_respond_read_key`](~peios-sdk/reference/rsi-response#read_key) |
| `DROP_KEY` | Delete the metadata record for `guid`. | status |
| `WRITE_KEY` | Update **only** the fields selected in `field_mask` — the SD when `RSI_WRITE_KEY_FIELD_SD` is set, the `last_write_time` when its bit is set — leaving the rest untouched. | status |

`WRITE_KEY`'s `field_mask` is the important detail: `sd` is `NULL` unless the SD bit is set, and `last_write_time` is meaningful only when the time bit is set, so consult the mask before reading either.

### Value operations

These operate on the typed values stored on a key, each written into a layer.

```c
/* QUERY_VALUES — read value_name (or all values when query_all) of guid. */
struct rsi_query_values {
    uint8_t     guid[16];
    const void *value_name;  uint32_t value_name_len;
    uint8_t     query_all;   /* 1 = every value (then value_name is ignored) */
};
int rsi_request_query_values(const struct rsi_request *req, struct rsi_query_values *out);

/* SET_VALUE — store value_name in layer_name with the given type/data. */
struct rsi_set_value {
    uint8_t     guid[16];
    const void *value_name;  uint32_t value_name_len;
    const void *layer_name;  uint32_t layer_name_len;
    uint32_t    value_type;
    const void *data;  uint32_t data_len;
    uint64_t    sequence;
    uint64_t    expected_sequence;  /* CAS guard (0 disables) */
};
int rsi_request_set_value(const struct rsi_request *req, struct rsi_set_value *out);

/* DELETE_VALUE_ENTRY — remove value_name's entry in layer_name. */
struct rsi_delete_value_entry {
    uint8_t     guid[16];
    const void *value_name;  uint32_t value_name_len;
    const void *layer_name;  uint32_t layer_name_len;
};
int rsi_request_delete_value_entry(const struct rsi_request *req,
                                   struct rsi_delete_value_entry *out);

/* SET_BLANKET_TOMBSTONE — set or clear a blanket tombstone on layer_name. */
struct rsi_set_blanket_tombstone {
    uint8_t     guid[16];
    const void *layer_name;  uint32_t layer_name_len;
    uint8_t     set;         /* 1 = set, 0 = clear */
    uint64_t    sequence;
};
int rsi_request_set_blanket_tombstone(const struct rsi_request *req,
                                      struct rsi_set_blanket_tombstone *out);
```

| Op | You must | Reply with |
|---|---|---|
| `QUERY_VALUES` | Return `value_name` — or every value when `query_all` is `1` (then `value_name` is ignored) — plus any blanket tombstones. | [`rsi_respond_query_values`](~peios-sdk/reference/rsi-response#query_values) |
| `SET_VALUE` | Store `value_name` of `value_type` in `layer_name`. Honour `expected_sequence` as a compare-and-swap guard (`0` disables it) — reject with a non-OK status if the current sequence differs. | status |
| `DELETE_VALUE_ENTRY` | Remove `value_name`'s entry in `layer_name`. | status |
| `SET_BLANKET_TOMBSTONE` | Set (`set == 1`) or clear a blanket tombstone on `layer_name`, masking all lower values at once. | status |

### Transaction operations

The kernel drives transaction boundaries; your source honours them so a group of writes commits or aborts atomically.

```c
/* BEGIN_TRANSACTION — open transaction_id in mode. */
struct rsi_begin_transaction {
    uint64_t    transaction_id;
    uint32_t    mode;   /* RSI_TXN_READ_WRITE (0) or RSI_TXN_READ_ONLY (1) */
};
int rsi_request_begin_transaction(const struct rsi_request *req,
                                  struct rsi_begin_transaction *out);

/* COMMIT_TRANSACTION / ABORT_TRANSACTION — a request carrying just a transaction id. */
struct rsi_transaction { uint64_t transaction_id; };
int rsi_request_commit_transaction(const struct rsi_request *req, struct rsi_transaction *out);
int rsi_request_abort_transaction(const struct rsi_request *req, struct rsi_transaction *out);
```

| Op | You must | Reply with |
|---|---|---|
| `BEGIN_TRANSACTION` | Open `transaction_id` in `mode` (`RSI_TXN_READ_WRITE` or `RSI_TXN_READ_ONLY`); buffer subsequent writes tagged with this id. | status |
| `COMMIT_TRANSACTION` | Atomically apply everything buffered under `transaction_id`. | status |
| `ABORT_TRANSACTION` | Discard everything buffered under `transaction_id`. | status |

Requests that belong to a transaction carry its id in `req.txn_id`; a `txn_id` of `0` means the request is outside any transaction.

### Layer operations

```c
/* DELETE_LAYER / FLUSH — a request carrying just a length-prefixed name. */
struct rsi_name { const void *name;  uint32_t name_len; };
int rsi_request_delete_layer(const struct rsi_request *req, struct rsi_name *out);
int rsi_request_flush(const struct rsi_request *req, struct rsi_name *out);
```

| Op | You must | Reply with |
|---|---|---|
| `DELETE_LAYER` | Remove the entire named layer, reporting the GUIDs of any keys it orphaned. | [`rsi_respond_delete_layer`](~peios-sdk/reference/rsi-response#delete_layer) |
| `FLUSH` | Durably persist pending writes for the named hive, replying only once persistence is confirmed. | status |

## See also

- **[`<rsi/response.h>`](~peios-sdk/reference/rsi-response)** — building the reply each op expects.
- **[Serving requests](~peios-sdk/registry-sources/serving-requests)** — the read/parse/dispatch/respond loop in full.
