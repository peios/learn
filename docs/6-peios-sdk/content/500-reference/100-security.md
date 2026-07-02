---
title: security.h — Security descriptors
type: reference
description: Complete reference for <peios/security.h> — the SID, security-descriptor, ACL, and ACE vocabulary shared by every KACS interface, plus the SDDL text codec and SD inheritance helpers.
related:
  - peios-sdk/getting-started/library-conventions
  - peios/identity/sids
  - peios/security-descriptors/overview
---

`<peios/security.h>` is the shared vocabulary of the whole access-control surface. SIDs, security descriptors, ACLs, and ACEs are the currency every KACS interface trades in — tokens carry them, files are protected by them, access checks evaluate them, and the registry secures keys with them. They cross the kernel boundary as variable-length, self-relative byte buffers in the MS-DTYP wire formats, and this module is the one place libpeios lifts that raw wire form into something safe to handle from C.

Everything here assumes the [library conventions](~peios-sdk/getting-started/library-conventions): `ssize_t` returns are byte lengths using the two-call protocol, builders are heap-backed and sticky-error, and views borrow the buffer they parse. This page does not repeat those rules per function — read that page first.

The module has four parts:

- **[SIDs](#sids)** — build, parse, format, and compare security identifiers.
- **[ACLs and security descriptors](#building-acls)** — assemble them with builders.
- **[Parsing](#parsing-views)** — read them back with zero-copy views.
- **[SDDL and inheritance](#sddl-text-codec)** — the text form and the userspace-only inheritance helpers.

The wire constants (`KACS_SID_*`, `KACS_SD_*`, `KACS_ACE_*`, and `struct kacs_generic_mapping`) come straight from `<pkm/sid.h>` and `<pkm/sd.h>`. libpeios does not re-alias them — you use the published ABI names directly.

## SIDs

A **SID** (Security Identifier) is the unique binary name of a principal. For the full account of what a SID *is* — its string and binary forms, the mixed endianness, the equality rule — see the operator-side page on [SIDs](~peios/identity/sids). This section is the API for handling them.

A SID is small and bounded. The largest possible encoding is `PEIOS_SID_MAX_BYTES` (68) bytes, so a buffer of that size holds any valid SID and the SID builders below never need a two-call probe — you can always pass a `PEIOS_SID_MAX_BYTES` stack buffer and skip straight to the retrieve call.

```c
#define PEIOS_SID_MAX_BYTES 68u
```

### Constructing SIDs

Each of these encodes a SID into your buffer and returns its length (or `-1` with `errno`). Because a SID fits in `PEIOS_SID_MAX_BYTES`, the probe is optional — but these are still `ssize_t`/two-call functions, so passing `cap == 0` to probe works too.

| Function | Builds |
|---|---|
| `peios_sid_build(out, cap, id_authority, sub_auths, count)` | An arbitrary SID from its parts: a 48-bit identifier authority (numeric, encoded big-endian) and `count` sub-authorities (encoded little-endian). `count` is `0..KACS_SID_MAX_SUB_AUTHORITIES`. |
| `peios_sid_parse_string(out, cap, sddl)` | A binary SID from its SDDL string form (`"S-1-5-21-…"`). |
| `peios_sid_integrity(out, cap, level_rid)` | An integrity-label SID `S-1-16-<rid>` (see [`peios_integrity_level`](#integrity-levels)). |
| `peios_sid_logon(out, cap, session_id)` | A logon SID `S-1-5-5-<hi>-<lo>` from a 64-bit session id. |
| `peios_sid_well_known(out, cap, which)` | A well-known SID selected by [`enum peios_wks`](#well-known-sids). |

```c
ssize_t peios_sid_build(void *out, size_t cap, uint64_t id_authority,
                        const uint32_t *sub_auths, unsigned count);
ssize_t peios_sid_parse_string(void *out, size_t cap, const char *sddl);
ssize_t peios_sid_integrity(void *out, size_t cap, uint32_t level_rid);
ssize_t peios_sid_logon(void *out, size_t cap, uint64_t session_id);
ssize_t peios_sid_well_known(void *out, size_t cap, enum peios_wks which);
```

`peios_sid_build` fails with `EINVAL` if `count` exceeds the maximum, and (like all of these) with `ERANGE` if a non-zero `cap` is too small.

### Formatting and inspecting SIDs

| Function | Returns |
|---|---|
| `peios_sid_format(sid, len, out, cap)` | The SDDL string form (`"S-1-…"`), as a string length excluding the `NUL` — allocate `len + 1`. |
| `peios_sid_valid(sid, len)` | `true` if `sid` is a structurally valid SID of *exactly* `len` bytes. |
| `peios_sid_length(sid)` | The encoded length of `sid`, read from its sub-authority count. **You must have already validated `sid`, or bounded it to `PEIOS_SID_MAX_BYTES`** — this trusts the buffer. |
| `peios_sid_equal(a, alen, b, blen)` | `true` for exact binary equality — the *only* equality KACS defines for SIDs. |
| `peios_sid_rid(sid, len)` | The RID (last sub-authority), or `0` if the SID has none. |

```c
ssize_t  peios_sid_format(const void *sid, size_t len, char *out, size_t cap);
bool     peios_sid_valid(const void *sid, size_t len);
size_t   peios_sid_length(const void *sid);
bool     peios_sid_equal(const void *a, size_t alen, const void *b, size_t blen);
uint32_t peios_sid_rid(const void *sid, size_t len);
```

The split between `peios_sid_valid` and `peios_sid_length` is deliberate: validation is the safe check that bounds an untrusted buffer; `peios_sid_length` is the fast reader you use *after* you trust the bytes (or when you have already capped the buffer at `PEIOS_SID_MAX_BYTES`). When in doubt, validate first.

### Well-known SIDs

`peios_sid_well_known` constructs any of the standard system principals without you memorising their numbers:

```c
enum peios_wks {
    PEIOS_WKS_NULL,                 /* S-1-0-0    Nobody */
    PEIOS_WKS_EVERYONE,             /* S-1-1-0    World */
    PEIOS_WKS_LOCAL,                /* S-1-2-0    Local */
    PEIOS_WKS_CREATOR_OWNER,        /* S-1-3-0 */
    PEIOS_WKS_CREATOR_GROUP,        /* S-1-3-1 */
    PEIOS_WKS_OWNER_RIGHTS,         /* S-1-3-4    suppresses owner WRITE_DAC */
    PEIOS_WKS_ANONYMOUS,            /* S-1-5-7 */
    PEIOS_WKS_SELF,                 /* S-1-5-10   PRINCIPAL_SELF */
    PEIOS_WKS_AUTHENTICATED_USERS,  /* S-1-5-11 */
    PEIOS_WKS_SYSTEM,               /* S-1-5-18   Local System */
    PEIOS_WKS_LOCAL_SERVICE,        /* S-1-5-19 */
    PEIOS_WKS_NETWORK_SERVICE,      /* S-1-5-20 */
    PEIOS_WKS_ADMINISTRATORS,       /* S-1-5-32-544 */
};
```

For the meaning of each principal, see [Well-known principals](~peios/identity/well-known-principals).

### Integrity levels

Integrity-label SIDs have the form `S-1-16-<rid>`, where the RID names a level. `peios_sid_integrity` takes that RID; the standard levels are:

```c
enum peios_integrity_level {
    PEIOS_IL_UNTRUSTED = 0,
    PEIOS_IL_LOW       = 4096,
    PEIOS_IL_MEDIUM    = 8192,
    PEIOS_IL_HIGH      = 12288,
    PEIOS_IL_SYSTEM    = 16384,
};
```

These are the labels that appear in a SACL as a `SYSTEM_MANDATORY_LABEL` ACE (see [`peios_acl_builder_label`](#adding-aces)).

## Access masks

An access mask is a 32-bit set of rights. Masks may contain four *generic* bits (`KACS_ACCESS_GENERIC_READ/WRITE/EXECUTE/ALL`) that stand in for object-specific rights until they are mapped to a concrete object class.

```c
uint32_t peios_access_map_generic(uint32_t mask,
                                  const struct kacs_generic_mapping *m);
```

`peios_access_map_generic` folds the generic bits of `mask` into object-specific rights using the mapping `m`, and clears the generic bits from the result. Each object class publishes its canonical mapping as a data symbol you pass here — `peios_file_generic_mapping` (from [`<peios/file.h>`](~peios-sdk/reference/file)) and `peios_token_generic_mapping` (from [`<peios/token.h>`](~peios-sdk/reference/token)). Use it when you have a mask written in generic terms (say, from an SDDL string using `GR`/`GW`) and need the concrete rights for a specific object type.

## Building ACLs

An **ACL** is an ordered list of ACEs. You assemble one with a `peios_acl_builder` — create it, add ACEs, take the serialised bytes, free it. Builders follow the [sticky-error rules](~peios-sdk/getting-started/library-conventions#memory-ownership): the adders return `void`, the first error latches, and you check `peios_acl_builder_error` at the end.

```c
typedef struct peios_acl_builder peios_acl_builder;

peios_acl_builder *peios_acl_builder_new(void);   /* NULL on OOM */
void               peios_acl_builder_free(peios_acl_builder *b);
void               peios_acl_builder_reset(peios_acl_builder *b);
```

`peios_acl_builder_reset` drops every accumulated ACE *and* clears the sticky error, so you can reuse one builder for several ACLs.

### Adding ACEs

The common single-SID families have convenience adders. `flags` is a mask of `KACS_ACE_FLAG_*` and is usually `0` — the flags carry inheritance semantics, which matter only for container/inheritable ACEs.

```c
void peios_acl_builder_allow(peios_acl_builder *b, const void *sid, size_t len,
                             uint32_t mask, uint8_t flags);
void peios_acl_builder_deny (peios_acl_builder *b, const void *sid, size_t len,
                             uint32_t mask, uint8_t flags);
void peios_acl_builder_audit(peios_acl_builder *b, const void *sid, size_t len,
                             uint32_t mask, uint8_t flags);
```

| Adder | Appends |
|---|---|
| `_allow` | An `ACCESS_ALLOWED` ACE — grants `mask` to `sid`. |
| `_deny` | An `ACCESS_DENIED` ACE — denies `mask` to `sid`. Order matters: put denies before allows. |
| `_audit` | A `SYSTEM_AUDIT` ACE — logs access by `sid` matching `mask`. Belongs in a SACL, not a DACL. |

For an integrity label there is a dedicated adder:

```c
void peios_acl_builder_label(peios_acl_builder *b, uint32_t integrity_rid,
                             uint32_t policy_mask);
```

It appends a `SYSTEM_MANDATORY_LABEL` ACE for integrity level `S-1-16-<integrity_rid>`. `policy_mask` is a mask of the `KACS_SYSTEM_MANDATORY_LABEL_NO_{READ,WRITE,EXECUTE}_UP` bits (from `<pkm/sd.h>`) that says which accesses a lower-integrity caller is denied. Like `_audit`, a label ACE belongs in a SACL.

For everything else — object ACEs, callback ACEs, resource-attribute ACEs — there is the general adder and a fully-specified ACE struct:

```c
struct peios_ace_spec {
    uint8_t       type;      /* KACS_ACE_TYPE_* */
    uint8_t       flags;     /* KACS_ACE_FLAG_* */
    uint32_t      mask;
    const void   *sid;       /* trustee */
    size_t        sid_len;
    const uint8_t *object_type;            /* 16-byte GUID, or NULL */
    const uint8_t *inherited_object_type;  /* 16-byte GUID, or NULL */
    const void   *app_data;  /* trailing callback/resource data */
    size_t        app_data_len;
};

void peios_acl_builder_add(peios_acl_builder *b, const struct peios_ace_spec *ace);
```

Fill in only the fields the `type` uses; leave the rest `NULL`/`0`:

- **Object ACEs** (`KACS_ACE_TYPE_*_OBJECT`) read `object_type` and `inherited_object_type` — each a 16-byte GUID, or `NULL` when absent.
- **Callback and resource-attribute ACEs** carry trailing `app_data` (which is `NULL` only when `app_data_len` is `0`). For callback ACEs this is the conditional-expression bytecode you can produce with [`peios_sddl_parse_condition`](#conditional-expressions).

The convenience adders are exactly `peios_acl_builder_add` with a pre-filled spec for the common cases; reach for `_add` when you need object, callback, or resource-attribute ACEs.

### Taking the ACL bytes

```c
const void *peios_acl_builder_bytes(peios_acl_builder *b, size_t *len_out);
ssize_t     peios_acl_builder_finish(peios_acl_builder *b, void *buf, size_t cap);
int         peios_acl_builder_error(const peios_acl_builder *b);
```

- `peios_acl_builder_bytes` borrows: it returns a pointer into the builder (valid until the next mutation, `_reset`, or `_free`), writing the length to `len_out` if non-`NULL`. It returns `NULL` if the sticky error is set.
- `peios_acl_builder_finish` copies the serialised ACL out using the two-call protocol.
- `peios_acl_builder_error` returns the latched errno, or `0` if the builder is healthy.

The usual next step is to hand these bytes to `peios_sd_builder_dacl` or `_sacl`.

## Building security descriptors

A **security descriptor** binds an owner, a group, a DACL, a SACL, and control flags into one self-relative buffer. Its builder mirrors the ACL builder's shape.

```c
typedef struct peios_sd_builder peios_sd_builder;

peios_sd_builder *peios_sd_builder_new(void);
void              peios_sd_builder_free(peios_sd_builder *b);
void              peios_sd_builder_reset(peios_sd_builder *b);
```

### Setting components

```c
void peios_sd_builder_owner(peios_sd_builder *b, const void *sid, size_t len);
void peios_sd_builder_group(peios_sd_builder *b, const void *sid, size_t len);
void peios_sd_builder_control(peios_sd_builder *b, uint16_t set, uint16_t clear);
void peios_sd_builder_dacl(peios_sd_builder *b, const void *acl, size_t len);
void peios_sd_builder_dacl_null(peios_sd_builder *b);
void peios_sd_builder_sacl(peios_sd_builder *b, const void *acl, size_t len);
```

- **Owner / group.** Omit the call to leave the component absent. That is exactly what you want when building a *partial* SD to set only some components via `kacs_set_sd` — the SD then carries only what you set.
- **Control bits.** `peios_sd_builder_control` sets the bits in `set` and clears those in `clear` (`KACS_SD_DACL_PROTECTED`, and friends). You do **not** manage `SELF_RELATIVE` or the `*_PRESENT` bits — the builder maintains those for you as you add components.
- **DACL / SACL.** Pass ACL bytes, typically straight from `peios_acl_builder_bytes`. An ACL with zero ACEs is a *present-but-empty* DACL, which grants only the owner's implicit rights.

The DACL has one subtlety worth stating plainly. KACS has **no NULL-DACL encoding** — there is no "DACL present, pointer null" form; the kernel's parser rejects it. So "grant everyone everything" is expressed as an **absent** DACL (the `DACL_PRESENT` control bit clear). `peios_sd_builder_dacl_null` requests exactly that: it clears any DACL you set earlier and produces the same bytes as never setting a DACL at all. It exists so you can state the grant-all intent explicitly rather than by omission — but be clear that it means *grant all*, not *deny all*.

### Taking the SD bytes

Identical in shape to the ACL builder:

```c
const void *peios_sd_builder_bytes(peios_sd_builder *b, size_t *len_out);
ssize_t     peios_sd_builder_finish(peios_sd_builder *b, void *buf, size_t cap);
int         peios_sd_builder_error(const peios_sd_builder *b);
```

`_bytes` borrows (valid until the next mutation/reset/free, `NULL` if errored), `_finish` copies out getxattr-style, `_error` returns the latched errno.

## Parsing — views

To *read* a security descriptor, ACL, or ACE you use zero-copy **views**. A view is a caller-allocated, opaque, stack-friendly struct that borrows the buffer you parse — see the [view rules](~peios-sdk/getting-started/library-conventions#memory-ownership). Every accessor that yields a SID, a nested ACL, or a blob returns a pointer *into the original buffer*, so that buffer must outlive the view and everything derived from it.

```c
typedef struct peios_sd_view        { uint64_t _opaque[8]; } peios_sd_view;
typedef struct peios_acl_view       { uint64_t _opaque[4]; } peios_acl_view;
typedef struct peios_ace_view       { uint64_t _opaque[4]; } peios_ace_view;
typedef struct peios_sid_array_view { uint64_t _opaque[4]; } peios_sid_array_view;
```

The `_opaque` arrays are sized for stack allocation with headroom — declare a view as a local and never read its fields.

### Security-descriptor views

```c
int      peios_sd_parse(const void *sd, size_t len, peios_sd_view *out);
uint16_t peios_sd_view_control(const peios_sd_view *v);
int      peios_sd_view_owner(const peios_sd_view *v, const void **sid, size_t *len);
int      peios_sd_view_group(const peios_sd_view *v, const void **sid, size_t *len);
int      peios_sd_view_dacl(const peios_sd_view *v, peios_acl_view *out);
int      peios_sd_view_sacl(const peios_sd_view *v, peios_acl_view *out);
```

`peios_sd_parse` validates a self-relative SD and populates `out`, returning `0` or `-1` (`EINVAL`). `peios_sd_view_control` returns the raw control-bit word.

The four component accessors return `0` with their out-params set on success, or `-1` if the component is **absent**. For the DACL and SACL, `-1` also covers the NULL-DACL case — since an absent DACL and a NULL DACL are the same thing in KACS, a `-1` from `peios_sd_view_dacl` uniformly means "no DACL constrains this object."

### ACL and ACE views

You can also parse a bare ACL directly — a token's default DACL, for instance, arrives as an ACL, not wrapped in an SD:

```c
int      peios_acl_parse(const void *acl, size_t len, peios_acl_view *out);
unsigned peios_acl_view_count(const peios_acl_view *a);
int      peios_acl_view_ace(const peios_acl_view *a, unsigned i, peios_ace_view *out);
```

`peios_acl_view_count` gives the number of ACEs; `peios_acl_view_ace` populates `out` for ACE `i` (0-based, in stored order), returning `0` or `-1` (`ERANGE` for an out-of-range index). Iterate in the obvious way:

```c
unsigned n = peios_acl_view_count(&dacl);
for (unsigned i = 0; i < n; i++) {
    peios_ace_view ace;
    peios_acl_view_ace(&dacl, i, &ace);
    /* inspect ace … */
}
```

Each ACE is read through its own accessors:

```c
uint8_t  peios_ace_view_type(const peios_ace_view *e);
uint8_t  peios_ace_view_flags(const peios_ace_view *e);
uint32_t peios_ace_view_mask(const peios_ace_view *e);
int      peios_ace_view_sid(const peios_ace_view *e, const void **sid, size_t *len);
int      peios_ace_view_object_type(const peios_ace_view *e, const uint8_t **guid16);
int      peios_ace_view_inherited_object_type(const peios_ace_view *e,
                                              const uint8_t **guid16);
int      peios_ace_view_app_data(const peios_ace_view *e, const void **data,
                                 size_t *len);
```

| Accessor | Yields |
|---|---|
| `_type` / `_flags` / `_mask` | The ACE's `KACS_ACE_TYPE_*` type, `KACS_ACE_FLAG_*` flags, and 32-bit access mask. |
| `_sid` | The trustee SID (a pointer into the buffer). `0` / `-1`. |
| `_object_type` | The object GUID of an object ACE — `0` with `*guid16` set to the 16 bytes, or `-1` if not present / not an object ACE. |
| `_inherited_object_type` | The inherited-object GUID, same convention. |
| `_app_data` | Trailing application data of a callback or resource-attribute ACE — for a callback ACE, this is the conditional-expression bytecode you can render with [`peios_sddl_format_condition`](#conditional-expressions). |

### SID-and-attributes arrays

Several token classes — `GROUPS`, `RESTRICTED_SIDS`, `DEVICE_GROUPS`, `CAPABILITIES` — return a packed `[count][sid_len][sid][attrs]…` blob rather than an ACL. Parse those with the SID-array view:

```c
int      peios_sid_array_parse(const void *blob, size_t len, peios_sid_array_view *out);
unsigned peios_sid_array_count(const peios_sid_array_view *a);
int      peios_sid_array_get(const peios_sid_array_view *a, unsigned i,
                             const void **sid, size_t *len, uint32_t *attrs);
```

`peios_sid_array_get` yields the `i`-th entry's SID (a pointer into the blob), its length, and its 32-bit attribute word (the `KACS_SE_GROUP_*` flags — enabled, mandatory, deny-only, and so on).

## SDDL text codec

The SDDL codec converts between the binary wire forms above and their human-readable SDDL text (MS-DTYP §2.5.1). This is a **pure-userspace facility** — the kernel speaks only binary — so it lives entirely in libpeios. All four entries use the two-call protocol (`cap == 0` to probe) and fail with `EINVAL` on malformed input.

```c
ssize_t peios_sddl_parse_sd(void *out, size_t cap, const char *sddl);
ssize_t peios_sddl_format_sd(char *out, size_t cap, const void *sd, size_t sd_len);
```

- `peios_sddl_parse_sd` parses SDDL text (e.g. `"O:SYG:BAD:(A;;FA;;;BA)"`) into self-relative SD wire bytes.
- `peios_sddl_format_sd` renders SD wire bytes back to a NUL-terminated SDDL string (length excludes the `NUL`, so allocate `len + 1`).

These are the friendliest way to construct a descriptor when you have one written down — parse the string rather than assembling ACEs by hand — and the friendliest way to log or display one.

### Conditional expressions

Callback ACEs carry a *conditional expression* as compiled "artx" bytecode. The codec converts between that bytecode and its SDDL expression text:

```c
ssize_t peios_sddl_parse_condition(void *out, size_t cap, const char *expr);
ssize_t peios_sddl_format_condition(char *out, size_t cap, const void *artx, size_t len);
```

- `peios_sddl_parse_condition` compiles an expression such as `@User.Title == "PM"` into the bytecode you place in a callback ACE's `app_data`.
- `peios_sddl_format_condition` renders bytecode back to text (with no outer parentheses), length excluding the `NUL`.

So the round trip for a conditional ACE is: write the condition as text → `peios_sddl_parse_condition` → put the bytecode in `peios_ace_spec.app_data` with a callback ACE `type` → add it to an ACL builder.

## SD inheritance

Inheritance — computing a child object's ACEs from its parent's inheritable ones — is also pure userspace (MS-DTYP §2.5.3.4). Both helpers take and produce self-relative SDs and use the two-call protocol.

```c
ssize_t peios_sd_reinherit(void *out, size_t cap, const void *parent_sd,
                           size_t parent_len, const void *child_sd,
                           size_t child_len, int is_container);
ssize_t peios_sd_strip_inherited(void *out, size_t cap, const void *sd,
                                 size_t sd_len, uint32_t info);
```

**`peios_sd_reinherit`** recomputes a child SD's inherited ACEs from its parent. It strips the ACEs carrying `ACE_FLAG_INHERITED` from the child DACL, re-derives them from the parent DACL, and appends them *after* the child's explicit ACEs; the child's owner, group, SACL, and control bits pass through unchanged. `is_container` is non-zero if the child is itself a container (which determines how container-inherit and object-inherit flags propagate). This is what you call when a parent's ACL changed and you need to push the new inheritance down to a child.

**`peios_sd_strip_inherited`** drops the `ACE_FLAG_INHERITED` ACEs from the ACLs selected by `info` — a mask of `*_SECURITY_INFORMATION` bits, of which `DACL_SECURITY_INFORMATION` and `SACL_SECURITY_INFORMATION` are honoured and the rest ignored (selecting neither copies the input verbatim). Owner, group, and control bits pass through. Use it to reduce a descriptor to just its *explicit* ACEs — for example before storing a "protected" descriptor that should not carry inherited entries.

Both return the new SD's byte length, or `-1` with `EINVAL` (malformed input) or `ERANGE` (a non-zero buffer too small).

## See also

- **[Library conventions](~peios-sdk/getting-started/library-conventions)** — the error, buffer, builder, and view rules this page builds on.
- **[SIDs](~peios/identity/sids)** and **[Security descriptors](~peios/security-descriptors/overview)** — the operator-side concepts behind this vocabulary.
- **[`<peios/token.h>`](~peios-sdk/reference/token)**, **[`<peios/file.h>`](~peios-sdk/reference/file)**, **[`<peios/access.h>`](~peios-sdk/reference/access)** — the KACS interfaces that consume this vocabulary, including the generic-mapping tables `peios_access_map_generic` expects.
