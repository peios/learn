---
title: Wire Format
---

This section defines the byte-level encoding of every message on the
three sockets (§6.1). It is normative: two independent implementations
MUST produce identical bytes for the same logical message, so that
third-party clients, sources, and administration tools interoperate.

## Framing and primitives

- Every message is exactly one `SOCK_SEQPACKET` datagram. There is no
  stream framing; the datagram boundary delimits the message.
- All integers are unsigned little-endian unless stated. `u8`/`u16`/
  `u32`/`u64` denote width; `i64` is a signed little-endian 64-bit
  value.
- **Strings** are encoded as `[len: u16][bytes: UTF-8]` (no NUL
  terminator). A length-prefixed string is written `str`.
- **SIDs** are encoded as `[len: u16][sid: binary SID per PSD-004 §2]`.
  A length-prefixed SID is written `sid`.
- **Timestamps** are `i64` Unix nanoseconds; the sentinel `-1` means
  "none"/"never".
- A token or other file descriptor is never in the datagram body; it is
  carried as ancillary data via `SCM_RIGHTS` (§6.1) and is described per
  message below.
- The total datagram length (12-byte envelope + body) MUST NOT exceed
  `AUTHD_MSG_MAX` = 65536 bytes; therefore `body_len` MUST equal
  `datagram_length − 12` and MUST NOT exceed 65524. A datagram violating
  either MUST be rejected with `INVALID_REQUEST` (§6.4.4) without partial
  processing.

## Envelope

Every request begins with a fixed 12-byte header:

```
struct request_header {
    u32 magic;       // 0x41555448  ("AUTH")
    u16 version;     // protocol version; this document defines 1
    u16 type;        // message type (§6.4.3)
    u32 body_len;    // bytes of body following the header
}
```

Every response begins with a fixed 12-byte header:

```
struct response_header {
    u32 magic;       // 0x41555448
    u16 version;     // echoes the request version
    u16 status;      // outcome (§6.4.4)
    u32 body_len;    // bytes of body following the header
}
```

`magic` is the `u32` value `0x41555448` (bytes `48 54 55 41` on the wire,
little-endian); it is compared as an integer, not as a byte string. A
server MUST reject a request whose `magic` is wrong, whose `version`
it does not implement (`UNSUPPORTED_VERSION`), or whose `body_len`
disagrees with the datagram length (`INVALID_REQUEST`).

## Message types

`type` values are partitioned by interface. A server MUST reject a type
that is not valid for the socket it arrived on with `INVALID_REQUEST`.

| Range | Interface | Type | Value |
|---|---|---|---|
| 1–15 | client (`/run/authd.sock`) | `LOGON` | 1 |
| | | `CHANGE_PASSWORD` | 2 |
| | | `QUERY` | 3 |
| | | `LOGON_ON_BEHALF` | 4 |
| | | `SESSION_MANAGE` | 5 |
| 16–31 | source verify/resolve (`…/sources/*.sock`) | `VERIFY_RESOLVE` | 16 |
| 32–63 | administration (`/run/lpsd.sock`) | `CREATE_USER` | 32 |
| | | `SET_PASSWORD` | 33 |
| | | `CREATE_GROUP` | 34 |
| | | `ADD_MEMBER` | 35 |
| | | `REMOVE_MEMBER` | 36 |
| | | `ENABLE_ACCOUNT` | 37 |
| | | `DISABLE_ACCOUNT` | 38 |
| | | `CHANGE_PASSWORD_SS` (self-service) | 39 |

## Status and reason codes

`status` (response header, `u16`) is the **client-visible** outcome:

| Status | Value | Meaning |
|---|---|---|
| `OK` | 0 | Success |
| `DENIED` | 1 | Authentication failed OR account state forbids logon — **undifferentiated** (§5.1, §3.3) |
| `MUST_CHANGE_PASSWORD` | 2 | Credential valid but expired (§5.1) |
| `LOGON_TYPE_DENIED` | 3 | Credential valid but the logon-rights gate denied this logon type (§5.2) |
| `NOT_AUTHORIZED` | 4 | The caller lacks the privilege required for this request (§6.3) |
| `INVALID_REQUEST` | 5 | Malformed, oversized, or wrong-for-socket |
| `UNSUPPORTED_VERSION` | 6 | `version` not implemented |
| `SOURCE_UNAVAILABLE` | 7 | The target source could not be reached |
| `POLICY_VIOLATION` | 8 | A write was refused by policy (e.g. ChangePassword vs §3.4) |
| `INTERNAL_ERROR` | 9 | Unexpected server failure |
| `RATE_LIMITED` | 10 | Throttled (§6.3) |
| `TOKEN_TOO_LARGE` | 11 | The assembled token's group set exceeds the kernel limit (§5.3) |

A **reason** code is recorded for audit only and **MUST NOT** be sent to
the client when the status is `DENIED`. It is carried in the audit event
(§5.1), never in the response body:

`NO_SUCH_PRINCIPAL`=0, `BAD_CREDENTIAL`=1, `ACCOUNT_DISABLED`=2,
`ACCOUNT_EXPIRED`=3, `ACCOUNT_LOCKED`=4 (carried as the trailing `u16
reason` on a source `DENIED`). Collapsing all of these to a single
client-visible `DENIED` with no reason is what closes the
account-enumeration and account-state oracles (§3.3, §5.1).

## Client message bodies

**`LOGON` request:**
```
u8   logon_type            // PSD-004 logon type (Interactive=2, …)
str  principal             // name in the grammar of §2.2
u16  cred_type             // 1 = password
u16  cred_len
u8[cred_len] credential    // raw credential bytes (for password, the UTF-8 password); length is the preceding cred_len, not separately prefixed
```
A `cred_type` not defined by this version (only `1` = password) MUST be
rejected with `INVALID_REQUEST` before any source call.

**`LOGON` response:** on `OK`, body =
```
u64  session_id
i64  pw_expiry_warning     // -1 if none; else nanoseconds until expiry
```
and the minted token fd is attached via `SCM_RIGHTS`. On any non-`OK`
status the body is empty and no fd is attached.

**`CHANGE_PASSWORD` request** (forwarded by authd to the source —
§2.2, §7.2):
```
str  principal
u16  old_len
u8[] old_password          // old_len bytes; may be 0 if caller holds account-admin privilege
u16  new_len
u8[] new_password
```
Response: `OK`, or `POLICY_VIOLATION` (rejected by §3.4), or `DENIED`
(old password wrong), or `NOT_AUTHORIZED`. Body empty.

**`LOGON_ON_BEHALF`, `QUERY`, `SESSION_MANAGE`:** the request bodies for
these are defined when their features land; for this version a server
MUST accept the type, enforce the gate of §6.3, and — for
`LOGON_ON_BEHALF` and `SESSION_MANAGE` beyond service-token mint — MAY
return `INVALID_REQUEST` for unimplemented sub-operations. The gates
themselves (§6.3) are normative now.

## Source verify/resolve body

**`VERIFY_RESOLVE` request** (authd → source) has the same field layout
as the `LOGON` request body above.

**`VERIFY_RESOLVE` response:** `status` is one of `OK`, `DENIED`,
`MUST_CHANGE_PASSWORD`, `SOURCE_UNAVAILABLE`, `INTERNAL_ERROR`. The
source includes the audit reason (above) in a trailing `u16 reason`
field of the response body **only** when status is `DENIED` (authd
forwards it to the audit event and strips it from the client response).
On `SOURCE_UNAVAILABLE` and `INTERNAL_ERROR` the body is empty.
On `OK` (and on `MUST_CHANGE_PASSWORD`, which still resolves identity for
the change flow) the body is the **resolved-principal record**:

```
sid   user_sid
u32   projected_uid          // the principal's id (§3.6); 0xFFFFFFFF if the source assigns none
u32   primary_group_rid
str   account_name
str   display_name         // empty string if none
str   upn                  // empty string if none
u32   account_flags        // §9
i64   pw_last_set
i64   pw_must_change        // -1 if not required
i64   account_expires       // -1 if never
u32   group_count
group_entry[group_count]   // each: { sid sid; u32 attributes; u32 gid }  (SE_GROUP_* per PSD-004; gid = the group's id, 0xFFFFFFFF if the source assigns none — authd resolves)
u32   claim_count
claim_entry[claim_count]   // each: { str name; u16 value_type; u16 value_len; u8[] value }
str   auth_package          // §5.3
str   logon_domain_name
sid   logon_domain_sid
```

The record carries no credential material and no signature (§4). The
`groups` array MUST be sorted in ascending **binary-SID order** — the
unsigned byte-wise `memcmp` of the binary SID encoding (PSD-004 §2) with
the `[len]` prefix excluded, the shorter encoding sorting first on a prefix
tie — and the `claims` array in ascending order of the UTF-8 bytes of
`name`, so the encoding is byte-identical across implementations. For this version
`claim_count` MUST be 0 (claims are deferred — §8); the `value_type` enum
is defined when claims land.

## Administration bodies

Administration requests (`/run/lpsd.sock`) share the envelope. Their
bodies are:

| Type | Body |
|---|---|
| `CREATE_USER` | `str account_name; str display_name; u32 account_flags;` then **optionally** `u16 new_len; u8[] new_password` (the initial password) — present iff bytes remain after `account_flags`, in which case they MUST form exactly that `u16 new_len; u8[new_len]` pair with no leftover (any other residue is `INVALID_REQUEST`); if absent the account is created with no password factor (a present `new_len = 0` decodes successfully but is rejected with `POLICY_VIOLATION` per §3.4, not `INVALID_REQUEST`) |
| `SET_PASSWORD` | `str principal; u16 new_len; u8[] new_password` (administrative reset; gated by account-admin privilege) |
| `CREATE_GROUP` | `str name; str display_name; u32 group_type` |
| `ADD_MEMBER` / `REMOVE_MEMBER` | `sid group_sid; sid member_sid` |
| `ENABLE_ACCOUNT` / `DISABLE_ACCOUNT` | `sid principal_sid` |
| `CHANGE_PASSWORD_SS` | identical to the client `CHANGE_PASSWORD` body |

`CREATE_USER` and `CREATE_GROUP` responses return, on `OK`, the assigned
`sid` of the new principal in the body. All administration responses use
the status codes of §6.4.4; a privilege-gate failure is `NOT_AUTHORIZED`.

## Versioning

A server MUST reject `version` values it does not implement with
`UNSUPPORTED_VERSION` rather than guessing. New fields are added by
incrementing `version`; within a version the layouts above are frozen.
