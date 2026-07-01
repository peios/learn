---
title: Reference Tables
---

This appendix consolidates the subsystem's enumerable artifacts. For
constants and default-policy tables the **values here are normative**
(the cited section defines their semantics and use); for syscalls,
sockets, and message types this appendix is an index into the normative
section.

## KACS syscalls used by authd

All are defined by PSD-004; numbers are from the generated UAPI
constants. authd is the only normal-operation caller (§2.1).

| Syscall | No. | Used for | Privilege | § |
|---|---|---|---|---|
| `kacs_create_logon_session` | 1004 | Create the logon session | `SeTcbPrivilege` | §5.3 |
| `kacs_create_token` | 1003 | Mint the token from the spec | `SeCreateTokenPrivilege` | §5.3 |
| `kacs_destroy_empty_logon_session` | 1006 | Roll back a session if minting fails | `SeTcbPrivilege` | §5.3 |
| `kacs_open_peer_token` | 1010 | Identify a connecting caller (race-free) | — | §6.2 |
| `kacs_impersonate_peer` | 1011 | Act as the caller for bounded work | — | §6.2 |
| `kacs_revert` | 1012 | End impersonation | — | §6.2 |
| `kacs_set_impersonation_level` | 1013 | Client caps server impersonation (no Rust wrapper yet) | — | §6.2, §8 |

## Sockets

Connect access is enforced by an explicit SD (§6.1) and by the
per-request gate (§6.3).

| Path | Listener | Type | Connect (allow) | § |
|---|---|---|---|---|
| `/run/authd.sock` | authd | `SOCK_SEQPACKET` | `S-1-5-11` (Authenticated Users), `S-1-5-18` (SYSTEM), `S-1-5-19`, `S-1-5-20` | §6.1 |
| `/run/authd/sources/<source>.sock` | the source | `SOCK_SEQPACKET` | authd's SID only | §6.1 |
| `/run/lpsd.sock` | lpsd | `SOCK_SEQPACKET` | `S-1-5-32-544` (Administrators), `S-1-5-18`, `S-1-5-11` (self-service only) | §6.1 |

The `/run/authd/sources/` **directory** SD MUST allow entry creation only
by the specific trusted source identities (e.g. lpsd's service SID may
create `lpsd.sock`; adpsd's may create `adpsd.sock`); creation MUST be
exclusive, and authd MUST verify each source socket is owned by its
expected identity before connecting (§6.1).

## Protocol message types and status codes

Normatively defined in §6.4. Message types: `LOGON`=1, `CHANGE_PASSWORD`=2,
`QUERY`=3, `LOGON_ON_BEHALF`=4, `SESSION_MANAGE`=5, `VERIFY_RESOLVE`=16,
`CREATE_USER`=32, `SET_PASSWORD`=33, `CREATE_GROUP`=34, `ADD_MEMBER`=35,
`REMOVE_MEMBER`=36, `ENABLE_ACCOUNT`=37, `DISABLE_ACCOUNT`=38,
`CHANGE_PASSWORD_SS`=39. Status codes: `OK`=0, `DENIED`=1,
`MUST_CHANGE_PASSWORD`=2, `LOGON_TYPE_DENIED`=3, `NOT_AUTHORIZED`=4,
`INVALID_REQUEST`=5, `UNSUPPORTED_VERSION`=6, `SOURCE_UNAVAILABLE`=7,
`POLICY_VIOLATION`=8, `INTERNAL_ERROR`=9, `RATE_LIMITED`=10, `TOKEN_TOO_LARGE`=11.
Audit-only reason codes (never sent to the client on `DENIED`):
`NO_SUCH_PRINCIPAL`=0, `BAD_CREDENTIAL`=1, `ACCOUNT_DISABLED`=2, `ACCOUNT_EXPIRED`=3, `ACCOUNT_LOCKED`=4 (§6.4).

## Request types and gates

| Interface | Request | Gate | § |
|---|---|---|---|
| `/run/authd.sock` | Logon | Knowledge of the credential (open) | §6.3 |
| `/run/authd.sock` | LogonOnBehalf | `SeTcbPrivilege` | §6.3 |
| `/run/authd.sock` | ChangePassword | Old-password knowledge OR account-admin | §6.3, §7.2 |
| `/run/authd.sock` | Query | Caller-impersonated | §6.3 |
| `/run/authd.sock` | Session management | `SeTcbPrivilege` | §6.3 |
| `/run/authd/sources/*.sock` | Verify/resolve | Peer is authd | §6.3 |
| `/run/lpsd.sock` | Create/Set/Add/Remove/Enable/Disable | Account-admin privilege | §7.2 |
| `/run/lpsd.sock` | ChangePassword (self-service) | Old-password knowledge OR account-admin | §7.2 |

## Default privilege-assignment table

Normative MVP default (§5.2). A token's present privileges are the union
over all its SIDs. **Reserved (never assigned to anyone):**
`SeCreateTokenPrivilege`, `SeTcbPrivilege`, `SeAssignPrimaryTokenPrivilege`,
and `SeLoadDriverPrivilege` (peinit-exclusive — PSD-004 MUST-strips it from
all non-peinit tokens; driver loading routes through peinit).

| SID | Assigned privileges (present) |
|---|---|
| SYSTEM `S-1-5-18` | all non-reserved privileges |
| Administrators `S-1-5-32-544` | SeBackup, SeRestore, SeTakeOwnership, SeSecurity, SeDebug, SeSystemtime, SeShutdown, SeSystemEnvironment, SeManageVolume, SeIncreaseBasePriority, SeProfileSingleProcess, SeCreatePermanent, SeCreateSymbolicLink, SeChangeNotify, SeImpersonate |
| Users `S-1-5-32-545` / Authenticated Users `S-1-5-11` | SeChangeNotify, SeCreateSymbolicLink, SeShutdown, SeTimeZone |
| LocalService `S-1-5-19` / NetworkService `S-1-5-20` | SeChangeNotify, SeImpersonate, SeCreateGlobal, SeAudit |
| Everyone `S-1-1-0`, Guest | (none) |

**Enabled-by-default:** `SeChangeNotifyPrivilege` only; every other
present privilege is present-but-disabled (§5.2).

## Default logon-rights table

Normative MVP default (§5.2). A principal may perform a logon type iff
some SID holds the allow right and no SID holds the deny right (deny
overrides). Deny lists are empty by default.

| Logon type | Allow (default) |
|---|---|
| Interactive (2) | `S-1-5-32-544`, `S-1-5-32-545` |
| Network (3) | `S-1-5-32-544`, `S-1-5-32-545` |
| Batch (4) | `S-1-5-32-544` |
| Service (5) | (assigned per service at install; none by default) |

## Implicit token groups by logon type

Normative (§5.2 step 2). Added by authd (not the kernel). Attribute set
`M` = `SE_GROUP_MANDATORY | SE_GROUP_ENABLED | SE_GROUP_ENABLED_BY_DEFAULT`
(per PSD-004).

| Group SID | When | Attrs |
|---|---|---|
| Everyone `S-1-1-0` | always | M |
| Authenticated Users `S-1-5-11` | iff `user_sid` ≠ Anonymous `S-1-5-7` | M |
| Local `S-1-2-0` | Interactive, Batch, Service | M |
| Interactive `S-1-5-4` | Interactive | M |
| Network `S-1-5-2` | Network | M |
| Batch `S-1-5-3` | Batch | M |
| Service `S-1-5-6` | Service | M |
| This Organization `S-1-5-15` | always | M |

## Integrity-level predicate

Normative MVP default (§5.2 step 4). Levels per PSD-004 §10.3.

| Condition (first match wins) | Level (RID) |
|---|---|
| user SID = SYSTEM `S-1-5-18` | System (0x4000) |
| token carries `S-1-5-32-544` | High (0x3000) |
| user SID = local Guest (RID 501) or Anonymous `S-1-5-7` | Low (0x1000) |
| otherwise | Medium (0x2000) |

## Constants and defaults

| Constant | Value | § |
|---|---|---|
| argon2id memory | 19456 KiB (19 MiB) | §3.3 |
| argon2id iterations (t) | 2 | §3.3 |
| argon2id parallelism (p) | 1 | §3.3 |
| argon2id salt length | 16 bytes (CSPRNG) | §3.3 |
| argon2id output length | 32 bytes | §3.3 |
| dummy verifier params | the live policy params | §3.3 |
| password min length | 12 | §3.4 |
| password max length | ≥ 64 (all printable Unicode incl. spaces) | §3.4 |
| password composition rules | none | §3.4 |
| breached/common-password blocking | deployment-configured list (MAY be empty); checked at set-password | §3.4 |
| password history depth | 0 (default) | §3.4 |
| password max age | none (default; admin may force `must_change`) | §3.4 |
| lockout threshold | 10 consecutive failures | §3.4 |
| lockout duration | 15 minutes | §3.4 |
| lockout reset | on success, or after the duration window | §3.4 |
| authd per-caller Logon budget | 30 attempts / 60 s sliding, then `RATE_LIMITED` | §6.3 |
| authd global Logon budget | 300 attempts / 60 s sliding, then `RATE_LIMITED` | §6.3 |
| recovery/built-in-Administrator lockout | exempt from remote-induced lockout (§3.4) | §3.4 |
| `machine_sid` | three `u32` sub-authorities from a CSPRNG, each non-zero | §3.1 |
| `object_guid` | UUIDv4 from a CSPRNG | §3.1 |
| RID allocation | monotonic from `rid_counter` (start 1000); never reused | §3.1 |
| token `default_dacl` | Owner: GENERIC_ALL; SYSTEM: GENERIC_ALL; + Administrators: GENERIC_ALL iff token carries `S-1-5-32-544` | §5.3 |
| token `owner` | the user SID | §5.3 |
| token `mandatory_policy` | `NO_WRITE_UP` | §5.3 |
| `auth_package` (lpsd) | `"Peios.Local"` | §5.3 |
| POSIX `uid`/`gid` projection | unified id space; derived per §3.6 | §3.6 |

## account_flags bits

Normative (§3.2). Bit positions in the `account_flags` `u32`.

| Bit | Flag |
|---|---|
| 0 | disabled |
| 1 | password-not-required |
| 2 | password-never-expires |
| 3 | smartcard-required |

Unassigned bits MUST be zero. `EnableAccount`/`DisableAccount` (§7.2)
toggle bit 0.

## POSIX id layout

Normative scheme in §3.6; all ids below 2³¹. The bands are the shared
allocation contract; the **Allocator** column names who assigns+stores in
each.

| Range | Meaning | Allocator |
|---|---|---|
| `0` | `S-1-5-18` SYSTEM (special case; `18` itself reserved) | computed |
| `1–999` | `S-1-5-N → N` (single-relative-id NT-authority principals — see the named list below) | computed |
| `1000–1999` | `S-1-5-32-N → 1000+N` (BUILTIN aliases) | computed |
| `65200–65299` | `S-1-2-N → 65200+N` (Local 65200, Console Logon 65201) | computed |
| `65530` | `S-1-1-0` (Everyone) | computed |
| `65534` | `S-1-0-0` (Null/Nobody; overflow sentinel); `65535` reserved | computed |
| `1,000,000–1,999,999` | fallback / orphan foreign SIDs | authd |
| `2,000,000–2,999,999` | service & virtual-host family: fixed roots `S-1-5-80-0`, `S-1-5-83-0`, `S-1-5-84-…`, `S-1-5-90-0`, `S-1-5-96-0` at the bottom, then per-instance `S-1-5-80-{hash}` / `83-{guid}` / `90-{n}` / `96-{n}` **allocated next-free** (no hashing — collision-free) | authd |
| `3,000,000–3,999,999` | AppContainer package SIDs `S-1-15-2-…` (future) | authd |
| `4,000,000–4,999,999` | capability SIDs `S-1-15-3-…` (future, gid-side) | authd |
| `5,000,000–9,999,999` | local namespace (`5,000,000 + rid`; `rid < 5,000,000`) | lpsd |
| `10,000,000 + 5,000,000·(dn−1)` | domain `dn` (reverse `dn = id ÷ 5,000,000 − 1`) | adpsd |

**Well-known `S-1-5-N` (band `1–999`, `→ N`):** 1 Dialup, 2 Network,
3 Batch, 4 Interactive, 6 Service, 7 Anonymous Logon, 8 Proxy,
9 Enterprise DCs, 10 Self, 11 Authenticated Users, 12 Restricted Code,
13 Terminal Server User, 14 Remote Interactive, 15 This Organization,
17 IUSR, 18 SYSTEM (→ `0`; `18` reserved), 19 LocalService,
20 NetworkService, 113 Local account, 114 Local account & Administrator.
(`5` is the logon-session family `S-1-5-5-X-Y`, not single-RID;
`21/32/64/65/80/83/84/90/96` are family prefixes, not principals.)

**`S-1-5-32-N` BUILTIN aliases (band `1000–1999`, `→ 1000+N`):** the full
544–580 set (Administrators 544→1544, Users 545, Guests 546, Power Users
547, Account/Server/Print/Backup Operators 548–551, Replicators 552,
Pre-Windows2000 554, Remote Desktop Users 555, … Remote Management Users
580). The arithmetic rule covers every alias.

**Domain-relative RIDs** (Administrator 500, Guest 501, krbtgt 502, Domain
Admins 512, Domain Users 513 … 527) are **not** a well-known band — they
are `namespace base + RID`: local 500/501 fall in the local band, domain
RIDs in the domain band.

## SID families with no id

These are omitted from the uid/gid projection entirely — they are never
object owners and KACS handles them SID-natively. A Linux view simply does
not show them.

- `S-1-3-*` — Creator Owner/Group/Server, Owner Rights (ACE placeholders).
- `S-1-4` and bare authority/domain prefixes (`S-1-5-21-…` with no RID,
  `S-1-5-32`, `S-1-5-80`, …) — identifier authorities/domains, not
  principals.
- `S-1-5-5-X-Y` — logon-session SIDs (per-session; isolation is
  SID-native — revisit only if a per-session Linux gid is ever needed).
- `S-1-5-64-*` (auth packages: NTLM/SChannel/Digest), `S-1-18-*` (asserted
  identity), `S-1-5-1000` (Other Organization) — authorization-context
  markers, never owners.
- `S-1-16-*` — mandatory integrity labels (not principals).

## group_type values

| Value | Meaning |
|---|---|
| 0 | security, domain-local (the only value lpsd uses this version) |

Other Windows scopes/types are reserved; clients SHOULD send 0.

## Reserved and well-known RIDs

| RID | Principal | § |
|---|---|---|
| 500 | built-in Administrator (created disabled) | §3.1 |
| 501 | built-in Guest (created disabled) | §3.1 |
| ≥ 1000 | allocated to new principals from `rid_counter` (never reused) | §3.1 |

`S-1-5-32` BUILTIN aliases (Administrators 544, Users 545, …) and other
well-known SIDs are defined by PSD-004 and represented as group entities
in lpsd (§3.1).

## `secret_part` protection schemes

| Scheme | Status | At-rest protection | § |
|---|---|---|---|
| `none` | this version | full-disk encryption of the volume | §3.5 |
| `tpm-sealed` | deferred | key sealed to measured boot (+ optional pepper) | §3.5, §8 |

## lpsd database tables

The principal-store schema (illustrative DDL, normative content) is
defined in §3.5: `domain`, `users`, `credentials`, `pw_history`,
`groups`, `members`, `claims`, `schema_version`.
