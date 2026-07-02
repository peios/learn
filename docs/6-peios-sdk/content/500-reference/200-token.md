---
title: token.h — Tokens and sessions
type: reference
description: Complete reference for <peios/token.h> — opening and minting access tokens, querying their contents, adjusting privileges and groups, duplicating/restricting/impersonating them, installing primary tokens, and managing logon sessions.
related:
  - peios-sdk/reference/security
  - peios-sdk/reference/access
  - peios/tokens/overview
  - peios/impersonation/overview
---

`<peios/token.h>` is the token surface of KACS. A **token** is the runtime object that carries an identity — a user SID, group SIDs, privileges, an integrity level, claims — and every access decision is made against one. This module lets you open the tokens that already exist (your own, another process's, a socket peer's), mint new ones, read their contents, transform them, and install or impersonate them.

**A token handle is a file descriptor.** Every open/create/duplicate call returns a raw `int` fd, `O_CLOEXEC` by default, that you close with `close()`. The `access` argument several calls take is the desired *handle-right* mask (`KACS_TOKEN_*`), access-checked against the token's own security descriptor and cached on the fd — a handle only lets you do what its rights allow.

The wire constants (`KACS_TOKEN_*`, `KACS_IMLEVEL_*`, `KACS_SE_*_PRIVILEGE`, `KACS_TOKEN_CLASS_*`, `KACS_LOGON_TYPE_*`) and the ioctl arg structs (`kacs_priv_entry`, `kacs_group_entry`) come from `<pkm/token.h>`. Query payloads that are SID arrays or ACLs are read with the [views in `<peios/security.h>`](~peios-sdk/reference/security#parsing-views).

The module divides into: **opening & creating**, the **token-spec builder**, **query**, **adjust/transform**, and **logon sessions**.

## Opening and creating tokens

Each of these returns a token fd (or `-1` with `errno`).

```c
int peios_token_open_self(unsigned flags, uint32_t access);
int peios_token_open_process(int pidfd, uint32_t access);
int peios_token_open_thread(int pidfd, int tid, uint32_t access);
int peios_token_open_peer(int conn_fd);
int peios_token_create_raw(const void *spec, size_t len);
```

| Function | Opens |
|---|---|
| `peios_token_open_self` | The calling thread's token. `flags` may be `KACS_TOKEN_OPEN_REAL` to get the **primary** token even while the thread is impersonating; otherwise you get the effective (impersonation-aware) token. `access` is the desired handle rights. |
| `peios_token_open_process` | The **primary** token of the process named by `pidfd`. Subject to a process-query access check and PIP dominance over the target. |
| `peios_token_open_thread` | Thread `tid`'s **impersonation** token if it is impersonating, else the process primary token. |
| `peios_token_open_peer` | The peer-identity token captured at `connect()` on a connected Unix stream/seqpacket socket `conn_fd` — how a server learns *who* is on the other end of a socket. The handle carries fixed `QUERY | IMPERSONATE` rights (no `access` argument). |
| `peios_token_create_raw` | Mints a token from a pre-built token-spec buffer. This is the escape hatch — **prefer the builder below**. Requires `SeCreateTokenPrivilege`. |

Errors, per call:

- **`peios_token_open_self`** — `EINVAL` (unknown `flags`; empty or unknown `access` bits), `EACCES` (the token's own SD denies `access`).
- **`peios_token_open_process`** — `EACCES` (any of the three checks failed — process-query right, PIP dominance, or the token SD; deliberately indistinguishable), `EBADF` (invalid pidfd), `ESRCH` (target exited), `EINVAL` (empty or unknown `access` bits).
- **`peios_token_open_thread`** — the `_open_process` set, plus `ESRCH` (thread exited, or not in `pidfd`'s process) and `EINVAL` (`tid <= 0`).
- **`peios_token_open_peer`** — `EACCES` (no captured peer token — an unconnected, datagram, or socketpair socket), `ENOTSOCK` (not a socket), `EBADF` (invalid fd).
- **`peios_token_create_raw`** — `EPERM` (privilege missing), `EINVAL` (spec failed kernel validation), `EFAULT` (bad spec pointer), `ENOMEM` (allocation failed).

`peios_token_open_peer` is the cornerstone of local authentication: accept a connection, open the peer token, and you have the caller's identity to query or impersonate — no password, no handshake, just the kernel's word for who connected.

## The token-spec builder

Minting a token means assembling a 192-byte-header wire format with many optional sections. The builder is the ergonomic path — typed setters, no hand-packed offsets — and follows the standard [sticky-error builder rules](~peios-sdk/getting-started/library-conventions#memory-ownership): the setters return `void`, the first error latches, you check `peios_token_builder_error` at the end, and you `_free` every builder.

```c
typedef struct peios_token_builder peios_token_builder;

peios_token_builder *peios_token_builder_new(void);
void                 peios_token_builder_free(peios_token_builder *b);
void                 peios_token_builder_reset(peios_token_builder *b);
```

### The index convention

Three fields — the owner, the primary group, and the restrict/deny indices — refer to SIDs *by index* into the token's own SID list rather than by value. The convention is fixed:

> **Index 0 is the user SID. Indices 1..N are the 1st..Nth group** you added with `peios_token_builder_add_group`, in order.

So to make the second group the primary group, you set `primary_group_index` to `2`. **Do not add the logon SID yourself** — the kernel injects it.

### Core fields

```c
void peios_token_builder_user(peios_token_builder *b, const void *sid, size_t len);
void peios_token_builder_add_group(peios_token_builder *b, const void *sid,
                                   size_t len, uint32_t attrs);
void peios_token_builder_privileges(peios_token_builder *b, uint64_t present,
                                    uint64_t enabled);
void peios_token_builder_type(peios_token_builder *b, uint8_t type, uint8_t imp_level);
void peios_token_builder_integrity(peios_token_builder *b, uint32_t rid);
void peios_token_builder_session(peios_token_builder *b, uint64_t session_id);
void peios_token_builder_owner_index(peios_token_builder *b, uint32_t index);
void peios_token_builder_primary_group_index(peios_token_builder *b, uint32_t index);
void peios_token_builder_default_dacl(peios_token_builder *b, const void *acl, size_t len);
```

| Setter | Sets |
|---|---|
| `_user` | The user SID (index 0). |
| `_add_group` | Appends a group SID with its `KACS_SE_GROUP_*` attribute word (enabled, mandatory, deny-only, …). Call once per group, in the order you want them indexed. |
| `_privileges` | The privilege bitmasks: `present` (which privileges the token holds) and `enabled` (which are on). Bits are `KACS_SE_*_PRIVILEGE`. |
| `_type` | The token `type` (`KACS_TOKEN_TYPE_*` — primary or impersonation) and, for an impersonation token, the impersonation level `imp_level` (`KACS_IMLEVEL_*`). |
| `_integrity` | The integrity level, as the RID of an `S-1-16-<rid>` label (see [`peios_integrity_level`](~peios-sdk/reference/security#integrity-levels)). |
| `_session` | The logon session id the token references. |
| `_owner_index` / `_primary_group_index` | Which SID (by [index](#the-index-convention)) is the default owner / primary group. |
| `_default_dacl` | The default DACL applied to new objects the token creates (ACL bytes, e.g. from a [`peios_acl_builder`](~peios-sdk/reference/security#building-acls)). |

### Advanced fields

These cover the rest of the token-spec and can be left unset. They are marked `[adv]` in the header for a reason — most tokens need none of them.

```c
void peios_token_builder_mandatory_policy(peios_token_builder *b, uint32_t bits);
void peios_token_builder_projected_ids(peios_token_builder *b, uint32_t uid, uint32_t gid);
void peios_token_builder_expiration(peios_token_builder *b, uint64_t when);
void peios_token_builder_source(peios_token_builder *b, const char name[8],
                                uint64_t source_id);
void peios_token_builder_audit_policy(peios_token_builder *b, uint32_t bits);
void peios_token_builder_add_restricted_sid(peios_token_builder *b, const void *sid,
                                            size_t len, uint32_t attrs);
void peios_token_builder_add_device_group(peios_token_builder *b, const void *sid,
                                          size_t len, uint32_t attrs);
void peios_token_builder_confinement(peios_token_builder *b, const void *sid, size_t len);
void peios_token_builder_supp_gids(peios_token_builder *b, const uint32_t *gids,
                                   unsigned count);
```

| Setter | Sets |
|---|---|
| `_mandatory_policy` | The mandatory-integrity policy bits governing how the integrity label is enforced. |
| `_projected_ids` | The POSIX `uid`/`gid` this token projects into the Linux-compatibility layer. |
| `_expiration` | An absolute expiry time after which the token is no longer valid. |
| `_source` | The token's source: an 8-byte `name` and a `source_id`, recording who issued it (appears in audit). |
| `_audit_policy` | Per-token audit policy bits. |
| `_add_restricted_sid` | Appends a restricting SID (a write-restricted / restricted token intersects these against the normal SIDs). |
| `_add_device_group` | Appends a device group SID (the device/machine side of a claim-aware token). |
| `_confinement` | The confinement/AppContainer package SID that sandboxes the token. |
| `_supp_gids` | Replaces the projected supplementary GIDs (pass `NULL, 0` to clear). |

### Token flags

The four boolean token-spec flags are set together, so a designated initialiser reads clearly:

```c
struct peios_token_flags {
    bool write_restricted;
    bool user_deny_only;
    bool isolation_boundary;
    bool confinement_exempt;
};
void peios_token_builder_flags(peios_token_builder *b, const struct peios_token_flags *f);
```

- `write_restricted` — the token's restricting SIDs are checked only for write access.
- `user_deny_only` — the user SID is usable for deny ACEs but not to grant access.
- `isolation_boundary` — marks an isolation boundary for confinement.
- `confinement_exempt` — the token is exempt from confinement checks.

### Claims

A **claim** is a named, typed, multi-valued security attribute — the input to conditional (callback) ACEs. Claims come in user and device flavours; both share the same shape.

```c
struct peios_token_claim_value {
    uint64_t    scalar;   /* INT64 / UINT64 / BOOLEAN (0 or 1) */
    const void *bytes;    /* STRING (UTF-8) / SID / OCTET */
    size_t      len;
};

struct peios_token_claim {
    const char *name;         /* UTF-8; transcoded to UTF-16LE on the wire */
    uint16_t    value_type;   /* KACS_CLAIM_TYPE_* */
    uint32_t    flags;        /* KACS_CLAIM_ATTR_* */
    const struct peios_token_claim_value *values;
    unsigned    value_count;
};

void peios_token_builder_add_user_claim(peios_token_builder *b,
                                        const struct peios_token_claim *claim);
void peios_token_builder_add_device_claim(peios_token_builder *b,
                                          const struct peios_token_claim *claim);
```

The `value_type` selects which member of each value carries the data:

| `value_type` | Value member |
|---|---|
| `KACS_CLAIM_TYPE_INT64` / `_UINT64` / `_BOOLEAN` | `scalar` (a boolean is `0` or `1`). |
| `KACS_CLAIM_TYPE_STRING` | `bytes`/`len` — a UTF-8 string (transcoded to UTF-16LE on the wire). |
| `KACS_CLAIM_TYPE_SID` | `bytes`/`len` — a binary SID. |
| `KACS_CLAIM_TYPE_OCTET` | `bytes`/`len` — an opaque blob. |

Each claim you add is round-tripped through the kernel's own claim parser before acceptance, so a malformed claim latches `EINVAL` on the builder immediately — you find out at build time, not at token-create time.

### LCS registry credentials

The final optional section grants the token registry-layer powers: which layer scopes it may resolve and which private layers it owns.

```c
struct peios_token_lcs_credentials {
    const uint8_t (*scope_guids)[16];    /* array of 16-byte GUIDs, each non-nil & unique */
    unsigned    scope_count;             /* <= KACS_TOKEN_LCS_MAX_SCOPE_GUIDS */
    const char *const *private_layers;   /* UTF-8 names, 1..255 bytes, no '/' or '\\', unique */
    unsigned    private_layer_count;     /* <= KACS_TOKEN_LCS_MAX_PRIVATE_LAYERS */
};
void peios_token_builder_lcs_credentials(peios_token_builder *b,
                                         const struct peios_token_lcs_credentials *creds);
```

Setting it replaces any prior credentials; it is emitted as the last token-spec section. See [`<peios/registry.h>`](~peios-sdk/reference/registry) for what layers and scopes mean.

### Finishing the builder

```c
ssize_t peios_token_builder_bytes(peios_token_builder *b, const void **out);
int     peios_token_builder_create(peios_token_builder *b);
int     peios_token_builder_error(const peios_token_builder *b);
```

- `peios_token_builder_bytes` returns the serialised length and, if `out` is non-`NULL`, writes a pointer into the builder (valid until the next reset/free) through it. Use this if you want the raw token-spec bytes.
- `peios_token_builder_create` does it in one step: serialise and mint, returning the new token fd. This is the usual call. It requires `SeCreateTokenPrivilege`.
- `peios_token_builder_error` returns the latched errno, or `0`.

Errors: `_bytes` and `_create` first surface any latched builder error — `EINVAL` (malformed field, SID, claim, or index) or `ENOMEM` (allocation failed). A clean `_create` then adds the `peios_token_create_raw` set: `EPERM` (privilege missing), `EINVAL` (spec failed kernel validation), `ENOMEM`.

```c
peios_token_builder *tb = peios_token_builder_new();
peios_token_builder_user(tb, user_sid, user_len);
peios_token_builder_add_group(tb, admins_sid, admins_len, KACS_SE_GROUP_ENABLED);
peios_token_builder_type(tb, KACS_TOKEN_TYPE_PRIMARY, 0);
peios_token_builder_integrity(tb, PEIOS_IL_MEDIUM);
peios_token_builder_session(tb, session_id);

int tok = peios_token_builder_create(tb);       /* -1 on failure */
if (tok < 0) { int e = peios_token_builder_error(tb); /* or errno */ }
peios_token_builder_free(tb);
```

## Query

You read a token's contents by **information class**. The generic reader handles any class getxattr-style; typed convenience wrappers cover the common ones.

```c
ssize_t peios_token_query(int fd, uint32_t info_class, void *buf, size_t cap);
ssize_t peios_token_user(int fd, void *sid_buf, size_t cap);   /* CLASS_USER */
```

- `peios_token_query` reads the class `info_class` (`KACS_TOKEN_CLASS_*`) into `buf` using the [two-call protocol](~peios-sdk/getting-started/library-conventions#the-two-call-buffer-protocol). Classes that return SID arrays or ACLs are parsed afterward with the [`<peios/security.h>` views](~peios-sdk/reference/security#parsing-views) — e.g. read `CLASS_GROUPS` into a buffer, then `peios_sid_array_parse` it.
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

## Adjust and transform

These change a token or derive a new one from it. Deriving calls return a new fd; in-place adjustments return `0` / `-1`.

### Privileges and groups

```c
int peios_token_adjust_privileges(int fd, const struct kacs_priv_entry *entries,
                                  unsigned count, uint64_t *prev_enabled);
int peios_token_reset_privileges(int fd);
int peios_token_adjust_groups(int fd, const struct kacs_group_entry *entries,
                              unsigned count, uint64_t *prev_state);
int peios_token_reset_groups(int fd);
```

- `peios_token_adjust_privileges` enables/disables the privileges named in `entries` (each a `kacs_priv_entry`); if `prev_enabled` is non-`NULL` it receives the prior enabled mask, so you can restore it later. `peios_token_reset_privileges` restores `enabled := enabled_by_default`. Errors: `EACCES` (handle lacks `ADJUST_PRIVILEGES`), `EINVAL` (empty or oversized batch, duplicate entry, enabling an absent privilege, unknown attribute bits), `EFAULT` (bad entries pointer).
- `peios_token_adjust_groups` is the group analogue. `prev_state`, if non-`NULL`, points at a caller array of `KACS_TOKEN_GROUP_MASK_WORDS` `uint64_t` words that receives the prior enabled bitmask. `peios_token_reset_groups` restores the default group state. Errors: `EACCES` (handle lacks `ADJUST_GROUPS`), `EINVAL` (mandatory, deny-only, or logon-SID group targeted; duplicate or out-of-range index; empty batch), `EFAULT` (bad entries pointer).

### Duplicate and restrict

```c
int peios_token_duplicate(int fd, uint32_t access, uint8_t type, uint8_t imp_level);

struct peios_token_restrict {
    uint64_t           privs_to_delete;
    const uint32_t    *deny_group_indices;   /* groups demoted to deny-only */
    unsigned           deny_count;
    const void *const *restrict_sids;        /* added restricting SIDs */
    const size_t      *restrict_sid_lens;
    unsigned           restrict_count;
    uint32_t           flags;                /* KACS_TOKEN_RESTRICT_WRITE_RESTRICTED */
};
int peios_token_restrict(int fd, const struct peios_token_restrict *spec);
```

- `peios_token_duplicate` copies the token, returning a new fd with handle rights `access`, token `type` (`KACS_TOKEN_TYPE_*`), and impersonation level `imp_level` (`KACS_IMLEVEL_*`). This is how you turn a primary token into an impersonation token, or narrow a handle's rights. Errors: `EACCES` (handle lacks `DUPLICATE`, or the new token's SD denies `access`), `EINVAL` (unknown `type`/`imp_level`, raising an impersonation token's level, empty or unknown `access` bits), `ENOMEM` (allocation failed).
- `peios_token_restrict` creates a **filtered** token — the sandboxing primitive. It can delete privileges (`privs_to_delete`), demote groups to deny-only (`deny_group_indices`, by [index](#the-index-convention)), add restricting SIDs (`restrict_sids`/`restrict_sid_lens`), and set `KACS_TOKEN_RESTRICT_WRITE_RESTRICTED`. The result is a strictly less-powerful token you can hand to less-trusted code. Errors: `EACCES` (handle lacks `DUPLICATE`), `EINVAL` (duplicate or out-of-range deny index, malformed restricting SID, unknown `flags`, `NULL` spec or arrays), `ENOMEM` (allocation failed).

### Impersonation and installation

```c
int peios_token_install(int fd);
int peios_token_impersonate(int fd);
int peios_token_revert(void);
```

- `peios_token_install` makes this **primary** token the calling process's primary token. Errors: `EACCES` (handle lacks `ASSIGN_PRIMARY`, or `SeAssignPrimaryTokenPrivilege` missing), `EINVAL` (not a primary token), `EAGAIN` (thread set changed mid-install — retry), `ENOMEM` (allocation failed).
- `peios_token_impersonate` makes this **impersonation** token the calling thread's effective identity — subsequent access checks on that thread run as the impersonated identity. Errors: `EACCES` (handle lacks `IMPERSONATE`), `EINVAL` (not an impersonation token), `EPERM` (restricted→unrestricted same-user — the one hard deny), `ENOMEM` (allocation failed).
- `peios_token_revert` undoes it: it clears the thread's impersonation token so checks run as the thread's real (primary) identity again. It takes no argument and is a no-op (reported as success) if the thread was not impersonating. This is the inverse of `peios_token_impersonate` — always pair them, ideally with `revert` in the cleanup path. Errors: none in normal operation.

The archetypal server flow: `peios_token_open_peer` the caller → `peios_token_impersonate` it → do the work as them → `peios_token_revert`.

### Linked tokens and defaults

```c
int peios_token_link(int elevated_fd, int filtered_fd, uint64_t session_id);
int peios_token_get_linked(int fd);
int peios_token_adjust_default(int fd, const void *dacl, size_t len,
                               uint16_t owner_index, uint16_t group_index);
int peios_token_set_session_id(int fd, uint32_t session_id);
```

- `peios_token_link` links an elevated + filtered primary-token pair in `session_id` — the UAC-style split-token model, where a filtered token is the everyday identity and its elevated linked token is available on demand. `peios_token_get_linked` opens the linked token of `fd`, returning a new fd. Errors (`_link`): `EACCES` (`SeTcbPrivilege` missing, or either handle lacks `DUPLICATE`), `EINVAL` (self-link, role/session/user-SID mismatch, not primary tokens, unknown `session_id`, or an fd that is not a token fd), `EBADF` (invalid fd). Errors (`_get_linked`): `EACCES` (handle lacks `QUERY`), `ENOENT` (not part of a linked pair, or the pair was destroyed), `ENOMEM` (allocation failed).
- `peios_token_adjust_default` replaces the token's default DACL and/or owner/primary-group indices. `dacl == NULL` leaves the DACL unchanged (and ignores `len`); `dacl != NULL` with `len == 0` clears it; an index of `0xFFFF` leaves that index unchanged. Errors: `EACCES` (handle lacks `ADJUST_DEFAULT`), `EINVAL` (out-of-range index; malformed or oversized DACL), `EFAULT` (bad DACL pointer).
- `peios_token_set_session_id` sets the token's session id (requires `SeTcbPrivilege`). Errors: `EACCES` (handle lacks `ADJUST_SESSIONID`, or `SeTcbPrivilege` missing).

## Logon sessions

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

## The generic mapping

```c
extern const struct kacs_generic_mapping peios_token_generic_mapping;
```

The canonical generic→specific rights mapping for the **token** object class. Pass it to [`peios_access_map_generic`](~peios-sdk/reference/security#access-masks) or as the `mapping` in a [`peios_access_request`](~peios-sdk/reference/access#the-request) when the object under check is a token.

## See also

- **[`<peios/security.h>`](~peios-sdk/reference/security)** — the SID/ACL/SD vocabulary and the views used to parse group and privilege query payloads.
- **[`<peios/access.h>`](~peios-sdk/reference/access)** — checking access with a token fd.
- **[Tokens](~peios/tokens/overview)** and **[Impersonation](~peios/impersonation/overview)** — the operator-side model.
