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
| 16–31 | source (`…/sources/*.sock`) | `VERIFY_RESOLVE` | 16 |
| | | `CHANGE_PASSWORD` (forwarded self-service) | 17 |
| | | `RESOLVE` (credential-less resolve) | 18 |
| 32–63 | administration (`/run/lpsd.sock`) | `CREATE_USER` | 32 |
| | | `SET_PASSWORD` | 33 |
| | | `CREATE_GROUP` | 34 |
| | | `ADD_MEMBER` | 35 |
| | | `REMOVE_MEMBER` | 36 |
| | | `ENABLE_ACCOUNT` | 37 |
| | | `DISABLE_ACCOUNT` | 38 |
| | | `ENTER_SETUP_MODE` | 39 |

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

**`CHANGE_PASSWORD` request** — self-service; authd routes it by the
principal's namespace (§2.2, exactly as for `LOGON`) and forwards it,
unmodified, to the resolved source's registered socket as the source-side
`CHANGE_PASSWORD` (type 17) below:
```
str  principal
u16  old_len
u8[] old_password          // old_len bytes; MUST be > 0 (knowledge of the old password is the authorization — §6.3)
u16  new_len
u8[] new_password
```
This verb is **self-service only**: the authorization is knowledge of the
old password, which rides in the body and so survives the forward.
Administrative reset (no old password, gated by the **Reset Password**
control-access right on the target's SD — §7.2) is **not** this message —
it is `SET_PASSWORD` (type 33), which is source-shaped and goes
**directly** to the admin socket where the source captures the caller's
own peer token and AccessChecks it (§2.2, §7.2). An `old_len` of
0 here is `INVALID_REQUEST`.
Response: `OK`, `POLICY_VIOLATION` (rejected by §3.4), `DENIED` (uniform —
old password wrong, no such principal, or account locked/disabled; §3.3),
`RATE_LIMITED` (throttled before forwarding — §6.3), or
`SOURCE_UNAVAILABLE`. Body empty.

**`LOGON_ON_BEHALF` request** — the credential-less service logon (§5.4),
gated on the peer holding `SeTcbPrivilege` (§6.3):
```
u8   logon_type              // MUST be Service (5) this version; any other value is INVALID_REQUEST
sid  target                  // the identity to mint: a base service identity (SYSTEM S-1-5-18, LocalService S-1-5-19, NetworkService S-1-5-20) or a machine_sid-relative service-account SID
u32  service_sid_count
sid[service_sid_count] service_sids   // S-1-5-80-… service SIDs to add to the token as groups (may be 0)
```
authd resolves `target` per §5.4: a base service identity is built from
the static catalogue + idmap with no source contacted; a
`machine_sid`-relative `target` MUST bear the service-account flag (§9)
and is resolved through the source's `RESOLVE` (below). A `target` that is
an ordinary user, a domain principal, a pseudo-principal, or an
`S-1-5-80` service SID (which is a group, never an identity) is
`INVALID_REQUEST`. Each `service_sids` entry MUST be an `S-1-5-80-…` SID
and is added to the token as a group (§5.4).

**`LOGON_ON_BEHALF` response:** mirrors the `LOGON` response — on `OK`,
body = `u64 session_id; i64 pw_expiry_warning` (`-1`), with the minted
token fd attached via `SCM_RIGHTS`. Non-`OK` (`DENIED` for a
disabled/expired service account, `INVALID_REQUEST`, `LOGON_TYPE_DENIED`,
`SOURCE_UNAVAILABLE`, `INTERNAL_ERROR`) carries an empty body and no fd.

**`QUERY`, `SESSION_MANAGE`:** the request bodies for these are defined
when their features land; for this version a server MUST accept the type,
enforce the gate of §6.3, and MAY return `INVALID_REQUEST` for
unimplemented sub-operations. The gates themselves (§6.3) are normative
now.

## Source bodies

The source socket carries the source-transparent operations authd brokers
on the caller's behalf: `VERIFY_RESOLVE` (type 16) and the forwarded
self-service `CHANGE_PASSWORD` (type 17). Both are authd→source and gated
by the peer being authd (§6.3); the source-shaped write operations
(`SET_PASSWORD` and the rest) are a separate interface on the admin socket
below.

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
sid   primary_group_sid
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

The record carries no credential material and no signature (§4), and
every group SID MUST be one the source is authoritative to assert (§4,
§5.2) — authd rejects a resolved principal that asserts a SID outside the
source's authority. authd also validates every projected id before minting:
non-sentinel ids MUST be below 2^31, lie in the correct §3.6/§9 band, and
reverse-map to the same SID; `0xFFFFFFFF` MUST be resolved through the idmap
and MUST NOT reach the token spec. The `groups` array MUST be sorted in ascending
**binary-SID order** — the
unsigned byte-wise `memcmp` of the binary SID encoding (PSD-004 §2) with
the `[len]` prefix excluded, the shorter encoding sorting first on a prefix
tie — and the `claims` array in ascending order of the UTF-8 bytes of
`name`, so the encoding is byte-identical across implementations. For this version
`claim_count` MUST be 0 (claims are deferred — §8); the `value_type` enum
is defined when claims land.

**`CHANGE_PASSWORD` request** (type 17; authd → source) has the same field
layout as the client `CHANGE_PASSWORD` body above (`str principal; u16
old_len; u8[] old_password; u16 new_len; u8[] new_password`), forwarded
unmodified. The source verifies the old password (the authorization — the
source captures authd as its peer, so the gate MUST be knowledge-based,
not peer-identity-based), applies the password policy of §3.4, and on
acceptance records the new verifier. That old-password verification runs
the **same lockout accounting, account-state gating, and dummy-verifier /
constant-time / uniform-`DENIED` enumeration resistance as a logon
verify** (§3.3, §3.4) — a wrong old password counts toward lockout, a
locked/disabled account or an unknown principal returns an indistinguishable
`DENIED`, and an expired password is still accepted (it is what the change
clears). An `old_len` of 0 MUST be rejected `INVALID_REQUEST` —
administrative reset is `SET_PASSWORD` on the admin socket, never this
verb.

**`CHANGE_PASSWORD` response:** `status` is one of `OK`,
`POLICY_VIOLATION` (§3.4), `DENIED` (uniform — old password wrong, no such
principal, or account locked/disabled; §3.3), `SOURCE_UNAVAILABLE`, or
`INTERNAL_ERROR`. Body empty. authd relays the status to the client
unchanged (and may itself return `RATE_LIMITED` before forwarding — §6.3).

**`RESOLVE` request** (type 18; authd → source) — the credential-less
resolve used by the service-logon path (§5.4) for a stored
service-account target. It carries **no credential**:
```
sid  principal                // the stored principal to resolve
```
The source checks account state (disabled/expired — §3.4) and, if the
account may be used, returns the resolved principal. It performs **no**
credential verification and **no** lockout/timing accounting.

**`RESOLVE` response:** `status` is `OK`, `DENIED` (account
disabled/expired; trailing `u16 reason` as for `VERIFY_RESOLVE`),
`SOURCE_UNAVAILABLE`, or `INTERNAL_ERROR`. On `OK` the body is the
**resolved-principal record** (identical layout to the `VERIFY_RESOLVE`
`OK` body above). There is no `MUST_CHANGE_PASSWORD` — no credential is in
play.

## Administration bodies

Administration requests (`/run/lpsd.sock`) share the envelope. Their
bodies are:

| Type | Body |
|---|---|
| `CREATE_USER` | `str account_name; str display_name; u32 account_flags;` then **optionally** `u16 new_len; u8[] new_password` (the initial password) — present iff bytes remain after `account_flags`, in which case they MUST form exactly that `u16 new_len; u8[new_len]` pair with no leftover (any other residue is `INVALID_REQUEST`); if absent the account is created with no password factor (a present `new_len = 0` decodes successfully but is rejected with `POLICY_VIOLATION` per §3.4, not `INVALID_REQUEST`). lpsd sets `primary_group_sid` to `S-1-5-32-545` and adds the new user to `BUILTIN\Users` (§3.2). |
| `SET_PASSWORD` | `str principal; u16 new_len; u8[] new_password` (administrative reset — no old password; gated by the **Reset Password** control-access right on the target's SD, AccessChecked against the caller's own peer token — §7.2. The direct, source-shaped counterpart to the forwarded self-service `CHANGE_PASSWORD`) |
| `CREATE_GROUP` | `str name; str display_name; u32 group_type` |
| `ADD_MEMBER` / `REMOVE_MEMBER` | `sid group_sid; sid member_sid` |
| `ENABLE_ACCOUNT` / `DISABLE_ACCOUNT` | `sid principal_sid` |
| `ENTER_SETUP_MODE` | Empty body. Accepted only before lpsd initialises a database, and only from the peinit bootstrap authority: a peer token holding `SeTcbPrivilege`, with user SID `S-1-5-18`, carrying the per-service SID for `peinit` when that SID is present (§7.1, §9). The request arms setup mode for this boot and causes lpsd to initialise the store exactly once; any repeat, any initialised database, any non-empty body, or any unauthorized peer is rejected. |

`CREATE_USER` and `CREATE_GROUP` responses return, on `OK`, the assigned
`sid` of the new principal in the body. All administration responses use
the status codes of §6.4.4; a privilege-gate failure is `NOT_AUTHORIZED`.
`ENTER_SETUP_MODE` returns `OK`, `NOT_AUTHORIZED`, `INVALID_REQUEST`, or
`INTERNAL_ERROR`, with an empty body.

## Versioning

A server MUST reject `version` values it does not implement with
`UNSUPPORTED_VERSION` rather than guessing. New fields are added by
incrementing `version`; within a version the layouts above are frozen.
