---
title: registry.h — The registry (LCS)
type: reference
description: "Complete reference for <peios/registry.h> — the LCS registry client: opening keys, reading and writing layered values, enumerating, watching for changes, securing keys, backup/restore, and transactions."
related:
  - peios-sdk/reference/security
  - peios-sdk/getting-started/library-conventions
  - peios/the-registry/overview
---

`<peios/registry.h>` is the client surface of **LCS** — the Layered Configuration Subsystem, Peios's kernel-mediated registry. LCS is modelled on the Windows registry: a hierarchy of **keys** (each with an immutable GUID identity and secured by its own KACS security descriptor) holding typed **values**. Its distinguishing feature is **layers**: every write is tagged with a precedence-ordered layer, and the *effective* view of a value resolves to the highest-precedence entry. That is what lets a base configuration, a site overlay, and a machine-local override coexist on one key and resolve deterministically.

This header is the registry **client**: open keys, read and write values, enumerate, watch, secure, back up, and run transactions. It does **not** cover the registry *source* (the storage backend) side — `REG_SRC_REGISTER` and the RSI framed protocol — which is a separate library, [**librsi**](~peios-sdk/registry-sources/overview). A client speaks only the syscalls and ioctls here.

**Handles are fds.** Three calls create file descriptors — `peios_reg_open_key`, `peios_reg_create_key`, and `peios_reg_begin_transaction`; everything else is an operation on a key fd or transaction fd, gated on the access right granted when the key was opened. The wire constants — value types (`REG_SZ` … `REG_QWORD`), key access rights (`KEY_*`), open/create flags, transaction states (`REG_TXN_*`), watch filters (`REG_NOTIFY_*`), and security-info bits — come from `<pkm/lcs.h>`.

## The buffer convention here

Most of libpeios returns variable-length data with an `ssize_t` and the [two-call protocol](~peios-sdk/getting-started/library-conventions#the-two-call-buffer-protocol). The registry's *reads* use the same idea but express it through **descriptor structs** rather than a return value, because a single read often fills more than one buffer (a value's data *and* its layer name, say). The pattern:

- Each read takes a descriptor struct with `*_cap` fields (in) and `*_len` fields (out), plus buffer pointers.
- On success it returns `0` and writes the actual length into each `*_len`.
- If a buffer is too small it returns `-1` with `errno == ERANGE` and writes the **required** length into the matching `*_len` — so a **zero-capacity buffer probes the size**.
- A `NULL` buffer is valid only with zero capacity; `NULL` with a nonzero capacity is `EINVAL`.
- For a read with two buffers, `ERANGE` is returned if *either* is too small, and *both* required lengths are reported, so one probe sizes everything.

Everything else follows the usual Linux convention: `0` / `-1` + `errno`.

## Opening and creating keys

```c
int peios_reg_open_key(int parent_fd, const char *path, uint32_t desired_access,
                       uint32_t flags);
int peios_reg_create_key(int parent_fd, const char *path, uint32_t desired_access,
                         uint32_t flags, const char *layer, int txn_fd,
                         uint32_t *disposition_out);
```

Both resolve `path` (NUL-terminated) against `parent_fd` — a key fd for a relative path, or `< 0` for an absolute path — and return a key fd **whose granted access mask is fixed for its lifetime** (like a file fd, so it can be delegated). `desired_access` is the requested `KEY_*` rights, checked against the key's SD.

- **`peios_reg_open_key`** opens an *existing* key. `flags` may be `REG_OPEN_LINK` to open a symlink key *itself* rather than following it. Errors: `ENOENT`, `EACCES`, `EINVAL`, `ELOOP`, `ENAMETOOLONG`, `ETIMEDOUT`, `EIO`, `ENOMEM`.
- **`peios_reg_create_key`** opens an existing key or creates a new one. `flags` may combine `REG_OPTION_VOLATILE` (a key that does not survive reboot) and `REG_OPTION_CREATE_LINK` (create a symlink key). `layer` names the target layer to create in (NUL-terminated), or `NULL` for the base layer. `txn_fd` enlists the create in a [transaction](#transactions), or `-1` to auto-commit. `disposition_out`, if non-`NULL`, receives `REG_CREATED_NEW` or `REG_OPENED_EXISTING`. Errors add `ENOSPC` and `EPERM` (privileged symlink creation) to the set above.

## Values

A value is **named** (length-counted; an empty name is the key's *default* value), **typed** (`REG_*`), and written **into a layer**. A base-layer target is `layer == NULL` with `layer_len == 0`; a non-`NULL` pointer with a zero length is rejected `EINVAL`.

### Reading a value

```c
struct peios_reg_value {
    uint64_t sequence;  /* out: effective entry's sequence number */
    void    *data;      /* in:  buffer for the value data (NULL to probe) */
    void    *layer;     /* in:  buffer for the layer name (NULL to probe/skip) */
    uint32_t type;      /* out: value type (REG_*) */
    uint32_t data_cap;  /* in */   uint32_t data_len;  /* out: actual/required */
    uint32_t layer_cap; /* in */   uint32_t layer_len; /* out: actual/required */
};

int peios_reg_query_value(int key_fd, const void *name, uint32_t name_len, int txn_fd,
                          struct peios_reg_value *v);
```

`peios_reg_query_value` reads the **effective** value `name` on `key_fd` — the winner of the layer precedence resolution. `name_len == 0` reads the default value; `txn_fd` reads within a transaction, or `-1` for none. It fills `v->data` with the value bytes and `v->layer` with the name of the layer that won, and reports the resolved `type` and `sequence`. Pass a `NULL` `layer` buffer if you don't care which layer won. Errors: `ENOENT` (no effective value, or a tombstone masks it), `ERANGE`, `EACCES`, `EINVAL`.

### Writing, deleting, tombstoning

```c
int peios_reg_set_value(int key_fd, const void *name, uint32_t name_len, uint32_t type,
                        const void *data, uint32_t data_len, const void *layer,
                        uint32_t layer_len, int txn_fd, uint64_t expected_seq);
int peios_reg_delete_value(int key_fd, const void *name, uint32_t name_len,
                           const void *layer, uint32_t layer_len, int txn_fd);
int peios_reg_blanket_tombstone(int key_fd, const void *layer, uint32_t layer_len,
                                int set, int txn_fd);
```

- **`peios_reg_set_value`** writes value `name` of `type` into a specific `layer` (`NULL`/`0` = base). `type` may be `REG_TOMBSTONE` to place a *per-value* tombstone that masks lower layers. `expected_seq` is a **compare-and-swap guard**: `0` disables it; otherwise the write applies only if the value's current sequence matches, else `EAGAIN`. This is how you do lost-update-safe read-modify-write — read the `sequence` from `peios_reg_query_value`, then set with `expected_seq` set to it. Errors: `EINVAL`, `EAGAIN`, `ENOSPC`, `ENAMETOOLONG`, `EPERM`, `EACCES`.
- **`peios_reg_delete_value`** removes *a layer's* entry for `name` (`NULL`/`0` = base). It is idempotent, and removing a layer's entry lets any lower-layer value **re-emerge** — deletion is per-layer, not global.
- **`peios_reg_blanket_tombstone`** sets (`set != 0`) or clears (`set == 0`) a *blanket* tombstone on a layer, masking **all** lower-precedence values of this key on that layer at once — the wholesale version of a per-value tombstone. `set` must be `0` or `1` (else `EINVAL`).

### Enumerating values

```c
int peios_reg_query_values_batch(int key_fd, int txn_fd, void *buf, uint32_t cap,
                                 uint32_t *len_out, uint32_t *count_out);

struct peios_reg_enum_value {
    void    *name;      /* in:  buffer for the value name (NULL to probe) */
    void    *data;      /* in:  buffer for the value data (NULL to probe) */
    uint32_t type;      /* out */
    uint32_t name_cap;  /* in */  uint32_t name_len;  /* out: actual/required */
    uint32_t data_cap;  /* in */  uint32_t data_len;  /* out: actual/required */
};
int peios_reg_enum_value(int key_fd, uint32_t index, int txn_fd,
                         struct peios_reg_enum_value *v);
```

Two ways to read every effective value of a key:

- **`peios_reg_query_values_batch`** reads them all into one `buf` in a single call — the efficient path. Each record is packed little-endian, back to back: `[name_len: u32][name][type: u32][data_len: u32][data]`, for `count` records. `len_out` receives the bytes written (or the required size on `ERANGE`); `count_out` receives the record count. Both may be `NULL`.
- **`peios_reg_enum_value`** reads one value at a time by `index`, dense over the key's tombstone-resolved values — walk from `0` until `ENOENT`. Use it when you want to process values incrementally rather than buffer them all.

## Subkeys, metadata, and watches

### Enumerating subkeys

```c
struct peios_reg_subkey {
    void    *name;             /* in:  buffer for the child's name (NULL to probe) */
    uint64_t last_write_time;  /* out: ns since the Unix epoch */
    uint32_t name_cap;         /* in */  uint32_t name_len;    /* out */
    uint32_t subkey_count;     /* out: the child's subkey count */
    uint32_t value_count;      /* out: the child's value count */
};
int peios_reg_enum_subkey(int key_fd, uint32_t index, int txn_fd,
                          struct peios_reg_subkey *v);
```

`peios_reg_enum_subkey` reads the child key at `index`, dense over visible children — walk from `0` until `ENOENT`. There is **no per-child access check** during enumeration (you see the names and counts; opening a child still checks its SD).

### Key metadata

```c
struct peios_reg_key_info {
    void    *name;                 /* in:  buffer for the key's leaf name (NULL to probe) */
    uint64_t last_write_time;      /* out */
    uint64_t hive_generation;      /* out: per-hive change epoch */
    uint32_t name_cap;  uint32_t name_len;
    uint32_t subkey_count;         /* out */
    uint32_t value_count;          /* out */
    uint32_t max_subkey_name_len;  /* out */
    uint32_t max_value_name_len;   /* out */
    uint32_t max_value_data_size;  /* out */
    uint32_t sd_size;              /* out: security-descriptor size */
    uint8_t  volatile_key;         /* out: 1 if volatile */
    uint8_t  symlink;              /* out: 1 if a symlink */
};
int peios_reg_query_key_info(int key_fd, struct peios_reg_key_info *v);
```

`peios_reg_query_key_info` reads the key's leaf name and its metadata (needs `READ_CONTROL`). Note the ordering wrinkle: the kernel reports the metadata **only once the name fits**, so a too-small (or zero-capacity) name buffer returns `ERANGE` with the required `name_len` and *no* metadata — size the name buffer from that, then call again to get everything. The `max_*` fields are sizing hints for enumerations; `hive_generation` is a per-hive change epoch you can watch to detect that *anything* under the hive changed.

### Deleting and hiding keys

```c
int peios_reg_delete_key(int key_fd, const void *layer, uint32_t layer_len, int txn_fd);
int peios_reg_hide_key(int key_fd, const void *layer, uint32_t layer_len, int txn_fd);
```

Both need `DELETE` access, take a layer (`NULL`/`0` = base) and an optional `txn_fd`, and cannot target a hive root (`EINVAL`).

- **`peios_reg_delete_key`** removes this key's path entry *in a layer*; lower-layer entries re-emerge. It fails with `ENOTEMPTY` if the key has visible children.
- **`peios_reg_hide_key`** creates a `HIDDEN` path entry that masks the key in a layer; removing that layer makes the key reappear. This is the key-level analogue of a tombstone — hide rather than destroy.

### Watching for changes

```c
int peios_reg_notify(int key_fd, uint32_t filter, int subtree);
int peios_reg_flush(int key_fd);
```

- **`peios_reg_notify`** arms change watches on `key_fd` (needs `KEY_NOTIFY`). `filter` is a mask of `REG_NOTIFY_VALUE` / `REG_NOTIFY_SUBKEY` / `REG_NOTIFY_SD` (or `REG_NOTIFY_ALL`); `subtree` (`0`/`1`) extends the watch to descendants. `filter == 0` disarms. Once armed, **the key fd itself becomes pollable** — `EPOLLIN` signals pending events, and `read()` on the fd returns the change records. So a watch integrates directly into an `epoll` loop with no side channel. Errors: `ENOENT` (orphaned key), `EINVAL`, `EACCES`.
- **`peios_reg_flush`** forces the source to persist this key's hive's pending writes (needs `KEY_SET_VALUE`) and returns once persistence is confirmed — the durability barrier.

**The change records.** A `read()` on an armed key fd returns as many **complete** records as fit in your buffer — records are never split across reads. If the buffer is too small for even the next record the read fails `EINVAL` (so size it generously — a few KiB), and a non-blocking fd with nothing pending fails `EAGAIN`. Each record is a little-endian, possibly unaligned byte stream (PSD-005 §11.2):

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `total_len` | Record size in bytes — advance by this to the next record (future versions may append fields). |
| 4 | 2 | `event_type` | `REG_WATCH_VALUE_SET` / `_VALUE_DELETED` / `_SUBKEY_CREATED` / `_SUBKEY_DELETED` / `_SD_CHANGED` / `_KEY_DELETED` / `_OVERFLOW`. |
| 6 | 2 | `name_len` | Byte length of `name`; `0` for the no-name events (`SD_CHANGED`, `KEY_DELETED`, `OVERFLOW`). |
| 8 | `name_len` | `name` | The changed value or subkey name (UTF-8, not NUL-terminated). |

A **subtree** watch appends two further fields after `name`: `path_depth` (`u16`) and that many length-prefixed path components (`u16` length + UTF-8 bytes), locating the changed key relative to the watched key — depth `0` means the watched key itself.

Delivery is best-effort with an overflow fallback: if records accumulate faster than you read them, the oldest are dropped and a `REG_WATCH_OVERFLOW` record is queued — on seeing one, re-read the watched key (and subtree) to recover current state rather than trusting the stream. Records describe **effective** (layer-resolved) changes, and uncommitted transactions produce none — events fire at commit.

## Key security descriptors

```c
int peios_reg_get_security(int key_fd, uint32_t security_info, void *sd, uint32_t cap,
                           uint32_t *sd_len_out);
int peios_reg_set_security(int key_fd, uint32_t security_info, const void *sd,
                           uint32_t sd_len, int txn_fd);
```

Keys are KACS-secured, so their SDs are read and written with the same [`<peios/security.h>`](~peios-sdk/reference/security) vocabulary as files and tokens; `security_info` selects components (owner/group/DACL/SACL).

- **`peios_reg_get_security`** reads the selected components into `sd` (KACS binary form), writing the length to `*sd_len_out` (may be `NULL`); a too-small buffer returns `ERANGE` with the required size there, and a zero `cap` probes. Owner/group/DACL need `READ_CONTROL`; the SACL needs `ACCESS_SYSTEM_SECURITY`.
- **`peios_reg_set_security`** applies the selected components of `sd`, merging with the rest (the kernel parses and validates). The DACL needs `WRITE_DAC`, the owner `WRITE_OWNER`, the SACL `ACCESS_SYSTEM_SECURITY`. Here `txn_fd` gives **atomicity, not layer qualification** (SDs are not layered), or `-1` to apply immediately. SD changes affect only **future** opens — handles already open keep their fixed grant.

## Backup and restore

```c
int peios_reg_backup(int key_fd, int output_fd);
int peios_reg_restore(int key_fd, int input_fd);
```

- **`peios_reg_backup`** exports the key and its entire subtree to `output_fd` (needs `SeBackupPrivilege`). It takes a read-only snapshot and performs no per-key access check — the privilege is the gate. Errors: `EPERM`/`EACCES`, `EBADF` (output not writable), `ENOENT`, `ENOTSUP`, `EBUSY`.
- **`peios_reg_restore`** replaces the key and its entire subtree from `input_fd` (needs `SeRestorePrivilege`), applied in **one transaction**. Errors: `EPERM`/`EACCES`, `EBADF` (input not readable), `EINVAL` (malformed stream), `EEXIST` (GUID collision), `EOVERFLOW`.

## Transactions

A transaction batches key creates and mutating value/key operations into an atomic unit.

```c
int peios_reg_begin_transaction(void);
int peios_reg_commit(int txn_fd);
int peios_reg_txn_status(int txn_fd, uint32_t *state_out, int *terminal_errno_out);
```

- **`peios_reg_begin_transaction`** starts one and returns a transaction fd (initially unbound; it binds to a source on first use), or `-1`/`ENOMEM`. Pass this fd as the `txn_fd` argument to the create and mutating calls to enlist them. **Closing the fd without committing aborts** the transaction — so a transaction is abort-by-default, which makes error paths safe.
- **`peios_reg_commit`** atomically applies everything enlisted. On success the fd is **terminal** — close it. Errors tell you what to do: `EINVAL` (already committed / never bound), `EBUSY` (write-lock contention — the transaction **stays active**, retry the commit), `EIO` (source failure — stays active), `ETIMEDOUT`.
- **`peios_reg_txn_status`** reads a transaction's state: `state_out` receives the `REG_TXN_*` state, and `terminal_errno_out` receives the errno that ended it (`0` while active or after a clean commit). Both may be `NULL`.

The lifecycle: `begin` → enlist operations by passing `txn_fd` → `commit` (retry on `EBUSY`/`EIO`) → `close`, or just `close` to abort.

## See also

- **[`<peios/security.h>`](~peios-sdk/reference/security)** — building and parsing the SDs that secure keys.
- **[Library conventions](~peios-sdk/getting-started/library-conventions)** — the base error and buffer rules the descriptor reads specialise.
- **[The registry](~peios/the-registry/overview)** — the operator-side model of layers, hives, and precedence.
