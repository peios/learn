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

**lpsd** additionally uses `kacs_open_peer_token` (§6.2) and
`kacs_access_check` / `kacs_access_check_list` (PSD-004 §10) to authorize
administration requests against the target object's stored SD (§7.2). It
holds no privilege and mints nothing. The SDs are stored in lpsd's own
database (the `sd` columns, §3.5), so lpsd does **not** use
`kacs_get_sd` / `kacs_set_sd` (those manage SDs on kernel objects) — it
passes the stored blob to AccessCheck directly.

## Sockets

Connect access is enforced by an explicit SD (§6.1) and by the
per-request gate (§6.3).

| Path | Listener | Type | Connect (allow) | § |
|---|---|---|---|---|
| `/run/authd.sock` | authd | `SOCK_SEQPACKET` | `S-1-5-11` (Authenticated Users), `S-1-5-18` (SYSTEM), `S-1-5-19`, `S-1-5-20` | §6.1 |
| `/run/authd/sources/<source>.sock` | the source | `SOCK_SEQPACKET` | authd's SID only | §6.1 |
| `/run/lpsd.sock` | lpsd | `SOCK_SEQPACKET` | `S-1-5-32-544` (Administrators), `S-1-5-18` | §6.1, §7.1 |

The `/run/authd/sources/` **directory** SD MUST allow entry creation only
by the specific trusted source identities (for v0.23, the lpsd SYSTEM
service token carrying lpsd's per-service SID may create `lpsd.sock`);
creation MUST be exclusive, and authd MUST verify each connected source's
peer token against the expected identity before trusting it (§6.1).

## Trusted daemon and source identities

Normative MVP table (§6.1, §7.1). Service SIDs are the deterministic
`S-1-5-80` per-service SIDs defined by PSD-007 for SYSTEM platform-service
tokens.

| Role | Socket / path | Expected peer identity | Authority |
|---|---|---|---|
| peinit bootstrap setup caller | `/run/lpsd.sock` `ENTER_SETUP_MODE` | SYSTEM (`S-1-5-18`) token holding `SeTcbPrivilege`, and the per-service SID for `peinit` if present; before that SID exists, the PSD-007 PID 1 bootstrap authority | May arm lpsd setup mode exactly once (§7.1) |
| lpsd source | `/run/authd/sources/lpsd.sock` | SYSTEM (`S-1-5-18`) service token carrying the per-service SID for `lpsd` | Local `machine_sid` namespace plus the `S-1-5-32` BUILTIN aliases lpsd hosts (§3.1, §5.2) |

Future sources (e.g. adpsd) MUST add a row before they may register. authd
MUST reject any source socket whose connected peer token does not match the
row for that source name.

## Protocol message types and status codes

Normatively defined in §6.4. Message types: `LOGON`=1, `CHANGE_PASSWORD`=2,
`QUERY`=3, `LOGON_ON_BEHALF`=4, `SESSION_MANAGE`=5, `VERIFY_RESOLVE`=16,
`CHANGE_PASSWORD` (source, forwarded)=17, `RESOLVE` (credential-less)=18,
`CREATE_USER`=32, `SET_PASSWORD`=33, `CREATE_GROUP`=34, `ADD_MEMBER`=35,
`REMOVE_MEMBER`=36, `ENABLE_ACCOUNT`=37, `DISABLE_ACCOUNT`=38,
`ENTER_SETUP_MODE`=39. Status
codes: `OK`=0, `DENIED`=1,
`MUST_CHANGE_PASSWORD`=2, `LOGON_TYPE_DENIED`=3, `NOT_AUTHORIZED`=4,
`INVALID_REQUEST`=5, `UNSUPPORTED_VERSION`=6, `SOURCE_UNAVAILABLE`=7,
`POLICY_VIOLATION`=8, `INTERNAL_ERROR`=9, `RATE_LIMITED`=10, `TOKEN_TOO_LARGE`=11.
Audit-only reason codes (never sent to the client on `DENIED`):
`NO_SUCH_PRINCIPAL`=0, `BAD_CREDENTIAL`=1, `ACCOUNT_DISABLED`=2, `ACCOUNT_EXPIRED`=3, `ACCOUNT_LOCKED`=4 (§6.4).

## Request types and gates

| Interface | Request | Gate | § |
|---|---|---|---|
| `/run/authd.sock` | Logon | Knowledge of the credential (open) | §6.3 |
| `/run/authd.sock` | LogonOnBehalf (Service logon, §5.4) | `SeTcbPrivilege` | §6.3 |
| `/run/authd.sock` | ChangePassword (self-service, forwarded) | Old-password knowledge | §6.3, §7.2 |
| `/run/authd.sock` | Query | Caller-impersonated | §6.3 |
| `/run/authd.sock` | Session management | `SeTcbPrivilege` | §6.3 |
| `/run/authd/sources/*.sock` | Verify/resolve, ChangePassword (forwarded), Resolve (credential-less) | Peer is authd | §6.3 |
| `/run/lpsd.sock` | Create/SetPassword/Add/Remove/Enable/Disable | AccessCheck of peer token vs the target's (or domain object's) SD (§7.2) | §7.2 |
| `/run/lpsd.sock` | EnterSetupMode | peinit bootstrap authority | §7.1 |

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

Normative (§5.2 step 1). Added by authd (not the kernel). Attribute set
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
| authd per-caller credential-attempt budget (Logon + ChangePassword) | 30 attempts / 60 s sliding, then `RATE_LIMITED` | §6.3 |
| authd global credential-attempt budget (Logon + ChangePassword) | 300 attempts / 60 s sliding, then `RATE_LIMITED` | §6.3 |
| recovery/built-in-Administrator lockout | exempt from remote-induced lockout (§3.4) | §3.4 |
| `machine_sid` | three `u32` sub-authorities from a CSPRNG, each non-zero | §3.1 |
| `object_guid` | UUIDv4 from a CSPRNG | §3.1 |
| RID allocation | monotonic from `rid_counter` (start 1000); never reused | §3.1 |
| CreateUser primary group | `S-1-5-32-545` (BUILTIN\Users) | §3.2 |
| CreateUser default membership | Add new user as a member of `S-1-5-32-545` | §3.2 |
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
| 4 | service-account (non-interactive; no credential; minted only via `LOGON_ON_BEHALF` — §5.4) |

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

## Principal-object access rights (AD-isomorphic)

Normative (§7.2). Administration is authorized by a KACS AccessCheck of
the caller's peer token against the target object's SD. The object-specific
(low-word) rights are AD's directory-service rights, adopted verbatim:

| Right | Value | Used for |
|---|---|---|
| `DS_CREATE_CHILD` | 0x00000001 | CreateUser/CreateGroup (on the domain object, class-scoped) |
| `DS_DELETE_CHILD` | 0x00000002 | delete a child (on the domain object) |
| `DS_LIST_CONTENTS` | 0x00000004 | enumerate (on the domain object) |
| `DS_SELF` | 0x00000008 | validated write (e.g. add-self to a group) |
| `DS_READ_PROP` | 0x00000010 | read a property/property-set (ObjectType-scoped) |
| `DS_WRITE_PROP` | 0x00000020 | write a property/property-set (ObjectType-scoped) |
| `DS_CONTROL_ACCESS` | 0x00000100 | invoke a control-access (extended) right (ObjectType = the right's GUID) |

Standard rights `DELETE`, `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER` are as
PSD-004 §3. A control-access (extended) right or a property-set is named by
the ACE's `ObjectType` GUID; class-scoping (which child class a create or
inheritance applies to) is the `InheritedObjectType` GUID. All GUIDs below
are **AD's own well-known values**, adopted for parity:

| Kind | Name | GUID |
|---|---|---|
| control-access | **Reset Password** (User-Force-Change-Password) | `00299570-246d-11d0-a768-00aa006e0529` |
| control-access | **Change Password** (User-Change-Password) | `ab721a53-1e2f-11d0-9819-00aa0040529b` |
| property-set | **User-Account-Restrictions** (account_flags, expiry) | `4c164200-20c0-11d0-a768-00aa006e0529` |
| property-set | **Membership** | `bc0ac240-79a9-11d0-9020-00c04fc2d3cf` |
| class | user | `bf967aba-0de6-11d0-a285-00aa003049e2` |
| class | group | `bf967a9c-0de6-11d0-a285-00aa003049e2` |

Verb → required access: CreateUser/CreateGroup = `DS_CREATE_CHILD`
class-scoped; SetPassword = `DS_CONTROL_ACCESS` + Reset-Password GUID;
self-service ChangePassword = `DS_CONTROL_ACCESS` + Change-Password GUID on
self (+ old-password knowledge); AddMember/RemoveMember = `DS_WRITE_PROP` +
Membership GUID (add-self MAY use `DS_SELF`); Enable/DisableAccount =
`DS_WRITE_PROP` + User-Account-Restrictions GUID; delete = `DELETE`.

## Default security descriptors

Normative MVP default (§7.1, §7.2). SID → granted rights; the domain
object's management ACEs are marked **inheritable** (`CONTAINER_INHERIT` +
`OBJECT_INHERIT`, class-scoped where noted) so they seed each new
principal's SD. Owner = Administrators; group = Administrators.

**Domain object (the container):**

| SID | Granted |
|---|---|
| SYSTEM `S-1-5-18` | full control (all rights) — grounds first-boot seeding (§7.1) |
| Administrators `S-1-5-32-544` | `DS_CREATE_CHILD`+`DS_DELETE_CHILD` (user & group classes), `DS_LIST_CONTENTS`, and — **inheritable** to principals — `DS_READ_PROP`, `DS_WRITE_PROP`, `DS_CONTROL_ACCESS` (all extended rights incl. Reset Password), `DELETE`, `WRITE_DAC` |
| Authenticated Users `S-1-5-11` | `DS_LIST_CONTENTS`, `DS_READ_PROP` (read), inheritable read to principals |

**Default principal SD** (stamped at CreateUser/CreateGroup, or equivalently the inherited result of the above):

| SID | Granted |
|---|---|
| SYSTEM `S-1-5-18` | full control |
| Administrators `S-1-5-32-544` | `DS_READ_PROP`, `DS_WRITE_PROP`, `DS_CONTROL_ACCESS` (incl. Reset Password), `DELETE`, `WRITE_DAC` |
| Self `S-1-5-10` | **Change Password** (`DS_CONTROL_ACCESS` + Change-Password GUID); `DS_READ_PROP` of general/public info. `S-1-5-10` resolves to the object's own SID at check time (PSD-004), so this grants the principal these rights on itself |
| Authenticated Users `S-1-5-11` | `DS_READ_PROP` (general/public info) |

Delegation is expressible now via the domain object's SD (§7.2); no named
preset (e.g. Account Operators) is shipped. Deferred (§8): a
**protected-accounts guardrail** — membership-based protected SDs
(AdminSDHolder-equivalent) that shield admin and built-in principals from
a broad delegation ACE — so until then, keep the tight default and
delegate narrowly. OU-scoped (sub-container) delegation is out of scope,
not deferred: lpsd is flat (§3), and hierarchical scoping is a
directory-source (adpsd) concept (§7.2).

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
`groups`, `members`, `claims`, `schema_version`. The `domain`, `users`,
and `groups` tables each carry an `sd` column (the object's KACS security
descriptor — §3.2, §7.2).
