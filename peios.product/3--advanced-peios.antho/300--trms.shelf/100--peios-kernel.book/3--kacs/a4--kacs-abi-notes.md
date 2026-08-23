---
title: KACS ABI Notes
description: What the KACS ABI tables cannot say for themselves — token query payload shapes, the specification names that differ from the headers, what is documented elsewhere, and the kernel configuration.
---

§3.A is generated from `pkm/uapi/pkm/` and holds only what a compiler
can measure. This appendix holds the rest: the two ACE types that have
a constant and no behaviour, the payload shapes behind the token query
classes, the specification spellings a reader may arrive holding, what
is deliberately documented elsewhere, and the kernel configuration
KACS is built by.

The split is structural rather than editorial. `gen-kacs-abi.py`
overwrites §3.A wholesale on every run, so anything written there is
lost the next time the ABI changes — which is exactly what happened to
two sections of this one before they were moved here.

## ACE types with no evaluator behaviour

Two of the ACE type constants in §3.A have a constant and nothing
behind it. The ACE parser in `kacs-core` dispatches on 0x00–0x03,
0x05–0x14 and classifies every other value as opaque, so an ACE of type
0x04 or 0x15 is skipped during evaluation and written back
byte-for-byte on serialisation. The constants exist so that a decoder
can put a name to the byte. libpeios' SDDL codec does, printing 0x15 as
`SYSTEM_ACCESS_FILTER`; the `sd` utility does not, and renders both as
`OTHER(0x04)` and `OTHER(0x15)`. PCDS §5.4 records the same state
normatively.

## Token query payloads

The class numbers come from the header and are tabulated in §3.A;
these are the payloads each one returns. Sizes are in bytes; a variable-length payload uses
the shapes below. An invalid class returns `EINVAL`.

Two repeating shapes appear throughout. A **SID array** is
`[count:u32le]` followed by `count` entries of
`[sid_len:u32le][sid_bytes][attributes:u32le]`, and reports a count of
zero when the array is empty rather than an empty payload. A **claims
array** is `[count:u32le]` followed by `count` entries of
`[entry_len:u32le][entry_bytes]`. A bare SID is the SID bytes alone,
and an absent optional SID or ACL is zero bytes.

| Class | Payload |
|---|---|
| `USER` | Bare SID. |
| `GROUPS` | SID array. |
| `PRIVILEGES` | 32 bytes: present, enabled, enabled-by-default and used, four `u64` in that order. |
| `TYPE` | `u32`, 4 bytes. |
| `INTEGRITY_LEVEL` | The mandatory-label SID `S-1-16-<level>`, 12 bytes. |
| `OWNER` | Bare SID, resolved through the owner index: 0 is the user SID, N is `groups[N-1]`. |
| `PRIMARY_GROUP` | Bare SID, resolved the same way. |
| `INTERACTIVITY_SCOPE` | `u32`, 4 bytes. |
| `RESTRICTED_SIDS` | SID array; count 0 on an unrestricted token. |
| `SOURCE` | 16 bytes: an 8-byte name followed by a `u64` LUID. |
| `STATISTICS` | 40 bytes: token id, LogonSession id, modified id, token type, a reserved zero, and expiration. |
| `ORIGIN` | `u64`, 8 bytes. |
| `ELEVATION_TYPE` | `u32`, 4 bytes. |
| `DEVICE_GROUPS` | SID array. |
| `APPCONTAINER_SID` | Bare SID; empty when the token is unconfined. |
| `CAPABILITIES` | SID array. |
| `MANDATORY_POLICY` | `u32`, 4 bytes. |
| `LOGON_TYPE` | `u32`, 4 bytes, read from the LogonSession. |
| `LOGON_SID` | Bare SID, derived from the LogonSession id. |
| `DEFAULT_DACL` | Binary ACL; empty when none is set. |
| `IMPERSONATION_LEVEL` | `u32`, 4 bytes. |
| `USER_CLAIMS` | Claims array. |
| `DEVICE_CLAIMS` | Claims array. |
| `PROJECTED_SUPPLEMENTARY_GIDS` | `[count:u32le]` followed by `count` `u32` GIDs. |

Nine token fields have no query class at all: `created_at`,
`token_guid`, `audit_policy`, `write_restricted`, `user_deny_only`,
`isolation_boundary`, `confinement_exempt`, the projected UID and GID
— only the supplementary GIDs are reportable —
`restricted_device_groups`, and the LCS registry credentials.

## Names that differ from the specifications

This manual uses the names `uapi/pkm/` declares, and the generated
tables of §3.A are authoritative for them. A reader may instead arrive
holding the name PCDS uses, which is MS-DTYP's — a legitimate spelling,
not an obsolete one, and the one a third party implementing PCDS will
have. This table maps those onto the headers.

| PCDS / MS-DTYP | uapi name |
|---|---|
| `ACCESS_ALLOWED_ACE_TYPE`, `SYSTEM_AUDIT_ACE_TYPE`, ... | `KACS_ACE_TYPE_ACCESS_ALLOWED`, `KACS_ACE_TYPE_SYSTEM_AUDIT`, ... (the qualifier moves to the front) |
| `KACS_REAL_TOKEN` | `KACS_TOKEN_OPEN_REAL` |
| `KACS_LEVEL_*` | `KACS_IMLEVEL_*` |
| `KACS_FILE_SUPERSEDE`, `_OPEN`, ... | `KACS_DISPOSITION_*` |
| `OWNER_SECURITY_INFORMATION`, ... | `KACS_SECINFO_*` |
| `SE_PRIVILEGE_ENABLED` / `_REMOVED` | `KACS_PRIVILEGE_ATTR_ENABLED` / `_REMOVED` |
| `KACS_PRIV_RESET_ALL_DEFAULTS` | `KACS_PRIVILEGE_RESET_ALL_DEFAULTS` |
| `KACS_RESTRICT_WRITE_RESTRICTED` | `KACS_TOKEN_RESTRICT_WRITE_RESTRICTED` |
| `SE_GROUP_*` | `KACS_SID_GROUP_*` |
| `TOKEN_CLASS_*` | `KACS_TOKEN_CLASS_*` |

The PIP tiers have no public names at all. The Protected type (512)
and the `PeiosTcb` trust level (8192) exist only as kernel-private
constants, and nothing in `uapi/pkm/` defines None, Protected or
Isolated. A program reasoning about tiers compares the numbers
(§3.7).

## What is not here

Required rights, error codes and validation rules are properties of
the implementation rather than of the headers, so they are documented
with the operations themselves: token rights and the per-ioctl
requirements in §3.2.8, the file rights in §3.9, the process rights
in §3.3.3, and the privileges in §3.4.2.

Two neighbouring ABIs are generated or documented separately.
`uapi/pkm/trace.h` is a versioned, append-only ABI of tracepoint
reason, operation and state codes intended for tooling.
`uapi/pkm/kmes.h` and `uapi/pkm/lcs.h` belong to their own chapters.

## Build configuration

`CONFIG_SECURITY_PKM=y` and `CONFIG_RUST=y` are required, as are
`CONFIG_STRICT_DEVMEM=y` and `CONFIG_MODULE_SIG_FORCE=y` -- the last
two enforced at initialisation rather than only at build (§3.7).
`CONFIG_SECURITY_SELINUX`, `_APPARMOR`, `_SMACK` and `_TOMOYO` are
refused by Kconfig dependency; `CONFIG_BPF_LSM` is refused only at
runtime, so a kernel enabling both configures and builds and then
fails to initialise. `CONFIG_LSM` is never parsed.

Two further symbols gate large bodies of code:
`CONFIG_SECURITY_PKM_KUNIT`, which compiles in the test harness and,
in the signing path, a different and publicly known verification key
(§3.6); and `CONFIG_STRATAFS_FS`, without which the copy-up API of
§3.9.7 is inert.
