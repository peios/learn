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

## ACE types with no evaluator behaviour [*abi-notes.opaque-ace-types]

Two of the ACE type constants in §3.A have a constant and nothing
behind it. The ACE parser in `kacs-core` dispatches on 0x00–0x03,
0x05–0x14 and classifies every other value as opaque, so an ACE of type
0x04 or 0x15 is skipped during evaluation and written back
byte-for-byte on serialisation. The constants exist so that a decoder
can put a name to the byte. libpeios' SDDL codec does, printing 0x15 as
`SYSTEM_ACCESS_FILTER`; the `sd` utility does not, and renders both as
`OTHER(0x04)` and `OTHER(0x15)`. PCDS §5.4 records the same state
normatively.

## Querying a token handle

The ioctl is straightforward in shape:

```
ioctl(token_fd, KACS_IOC_QUERY, &args)
```

Where `args` is a `kacs_query_args` struct:

| Field | Meaning |
|---|---|
| `token_class` | The numeric class identifying what to return (1–24 in v0.20). |
| `buf_len` | Input: the size of the output buffer in bytes. Output: the actual number of bytes the query needed. |
| `buf_ptr` | Userspace pointer to the output buffer. |

The kernel:

1. Validates the class against the catalog. Unknown classes return `-EINVAL`.
2. Checks that the fd grants `TOKEN_QUERY`. If not, returns `-EACCES`.
3. Computes the size the response needs.
4. If `buf_ptr` is zero or `buf_len` is zero — this is a **size query** — writes the required size to `buf_len` and returns 0.
5. If `buf_ptr` is non-zero but `buf_len` is smaller than required, returns `-ERANGE` with the required size still written to `buf_len`.
6. Otherwise writes the response to the buffer and returns 0.

The "two-call pattern" — size query then fetch — is the standard way to handle variable-length output:

1. Call once with `buf_ptr = NULL` (or `buf_len = 0`). The kernel writes the required size into `buf_len` and returns 0.
2. Allocate a buffer of the indicated size.
3. Call again with `buf_ptr` set to the buffer and `buf_len` set to its size. The kernel writes the response.

For classes with a fixed-size response, a single call with a buffer of the known size works in one go. The two-call pattern is needed only for classes whose response size depends on the token's contents (the groups class, the restricted-SIDs class, the default-DACL class, the claims classes).

The ioctl is idempotent — multiple queries for the same class produce the same result as long as the token has not been modified. Tokens carry a `modified_id` counter that increments on adjustment; if a query is part of a pipeline that depends on consistency across multiple queries, the `modified_id` can be queried first to detect mid-pipeline changes.


## Token query payloads [*abi-notes.token-query-payloads]

The class numbers come from the header and are tabulated in §3.A;
these are the payloads each one returns. Sizes are in bytes; a variable-length payload uses
the shapes below. An invalid class returns `EINVAL`. [*abi-notes.token-query-invalid-class]

Two repeating shapes appear throughout. A **SID array** is
`[count:u32le]` followed by `count` entries of
`[sid_len:u32le][sid_bytes][attributes:u32le]`, and reports a count of
zero when the array is empty rather than an empty payload. [*abi-notes.sid-array-shape] A **claims
array** is `[count:u32le]` followed by `count` entries of
`[entry_len:u32le][entry_bytes]`. [*abi-notes.claims-array-shape] A bare SID is the SID bytes alone,
and an absent optional SID or ACL is zero bytes. [*abi-notes.absent-optional-is-zero-bytes]

| Class | Payload |
|---|---|
| `USER` | Bare SID. |
| `GROUPS` | SID array. |
| `PRIVILEGES` | 32 bytes: present, enabled, enabled-by-default and used, four `u64` in that order. |
| `TYPE` | `u32`, 4 bytes. |
| `INTEGRITY_LEVEL` | The mandatory-label SID `S-1-16-<level>`, 12 bytes. |
| `OWNER` | Bare SID, resolved through the owner index: 0 is the user SID, N is `groups[N-1]`. [*abi-notes.owner-index-resolution] |
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

Several token fields have no query class at all: `created_at`,
`token_guid`, `audit_policy`, `write_restricted`, `user_deny_only`,
`isolation_boundary`, `confinement_exempt`, the projected UID and GID
— only the supplementary GIDs are reportable —
`restricted_device_groups`, and the LCS registry credentials. [*abi-notes.fields-without-query-class]

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
Isolated. [*abi-notes.pip-tiers-kernel-private] A program reasoning about tiers compares the numbers
(§3.7).

## Socket options and retired syscall numbers

Peer identity on AF_UNIX sockets is read and bounded through socket
options rather than syscalls. `uapi/pkm/socket.h` defines the option
level `SOL_KACS` (4096), its options `KACS_SO_PEER_TOKEN`,
`KACS_SO_IMPERSONATION_LEVEL`, `KACS_SO_PASS_TOKEN` and
`KACS_SO_RESTAMP`, and the ancillary message type `KACS_SCM_TOKEN`,
which travels at
`cmsg_level SOL_KACS` (§3.A). [*abi-notes.scm-token-cmsg-level] The kernel dispatches the option level
in `net/socket.c` ahead of the protocol's own handlers (patch
`net/socket-sol-kacs-dispatch.patch`), so the options reach KACS on
every socket family and KACS decides which it supports. [*abi-notes.sol-kacs-dispatch-all-families] The ancillary
message is carried per skb on AF_UNIX: `net/scm-kacs-token.patch`
gives `struct scm_cookie` a counted token reference and parses
`SOL_KACS` control messages; `net/af_unix-kacs-token.patch` carries
the reference on `struct unix_skb_parms`, stops a stream read at an
identity boundary, and advances the register at the point of
consumption. Everything KACS-specific behind those hooks lives in
`kacs/socket.c`. The semantics and error codes are in §3.5.3.

System V IPC objects carry descriptors of their own (§3.11); their
rights are `uapi/pkm/ipc.h`, and the same header defines the
`KACS_SD_AT_SYSV_*` flags that let `kacs_get_sd` and `kacs_set_sd`
address such an object by kind and id (`dirfd` carries the id, the
path is NULL). [*abi-notes.sysv-sd-at-addressing] The lookup is `ipc_lsm_with_object`, exported from
`ipc/util.c` by `ipc/util-lsm-with-object.patch`; the hooks themselves
are the LSM's own IPC hooks and need no patch.

Three syscall numbers are retired and left as permanent holes:
1010 (`kacs_open_peer_token`), 1011 (`kacs_impersonate_peer`) and
1013 (`kacs_set_impersonation_level`). A binary built against them
gets `ENOSYS`. [*abi-notes.retired-syscalls-enosys] The first became `getsockopt(SOL_KACS,
KACS_SO_PEER_TOKEN)`, the third `setsockopt(SOL_KACS,
KACS_SO_IMPERSONATION_LEVEL)`, and the second was a fusion of the
first with `KACS_IOC_IMPERSONATE` that now lives in libpeios as
`peios_token_impersonate_peer`.

## Open-interface documentation discrepancies

The sources below disagree or leave details uncorroborated. This records
**documentation differences, not a reconciled contract**. No runtime behavior
or version boundary was determined. The generated ABI supplies layouts and
constants; it does not settle these behavioral questions.

Source labels and line numbers refer to the `learn` snapshot
`4b119864d7f51c569ae1ac1932e4430f06731cf2`:

- **O:** the former Security Fundamentals [Opening files source](https://github.com/peios/learn/blob/4b119864d7f51c569ae1ac1932e4430f06731cf2/peios.product/1--security-fundamentals.antho/200--access-control.shelf/500--file-access.topic/300--opening-files.md), retained in that revision's history.
- **N:** [KACS-Native Open](~peios/advanced-peios/peios-kernel/kacs/facs/native-open), TRM §3.9.2.
- **L:** [Legacy Open Compatibility](~peios/advanced-peios/peios-kernel/kacs/facs/legacy-open), TRM §3.9.3.
- **D:** [Opening a file](~peios/sdk-files/opening-a-file), SDK reference.
- **G:** [Securing files](~peios/sdk-access-control/securing-files), SDK guide.

The links reach the current references; the line numbers identify the
comparison snapshot above.

1. **Maximum allowed.** O:116–127 says `MAXIMUM_ALLOWED` returns the
   maximum mask without checking the other requested bits, which it calls
   hints; N:14–19 says the concrete data/execute bits must be granted.
   Both require a concrete bit and reject `MAXIMUM_ALLOWED` alone. The
   general [DACL walk](~peios/advanced-peios/peios-kernel/kacs/access-check/dacl-walk#maximum-allowed)
   describes a separate AccessCheck layer and cannot settle open validity
   by analogy.

2. **Legacy masks.** O:135–145 maps `O_RDONLY` to
   `FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL | SYNCHRONIZE`,
   `O_WRONLY` to
   `FILE_WRITE_DATA | FILE_WRITE_ATTRIBUTES | FILE_WRITE_EA | READ_CONTROL | SYNCHRONIZE`,
   and `O_RDWR` to their union. O:154–158 makes only `FILE_READ_DATA` core
   for read-only opens and allows `FILE_READ_ATTRIBUTES` to be dropped.
   L:16–37 instead makes `FILE_READ_ATTRIBUTES` core with read data, write
   data, or both according to the flag; L:39–49 lists broader compat rights.
   O:138 says `O_APPEND` adds `FILE_APPEND_DATA`; L:30–33 replaces core
   `FILE_WRITE_DATA` with it, then re-adds write data for `O_TRUNC`.
   L:44–45 also requests write data as optional compat access on append
   opens. These are different mappings, not interchangeable summaries.

3. **Creator descriptors.** O:96–97 groups open-existing branches under
   `EINVAL` and lists `SUPERSEDE` only for an absent target. N:133–144
   distinguishes `FILE_OPEN` (`EOPNOTSUPP`) from existing
   `FILE_OPEN_IF`, `FILE_OVERWRITE` and `FILE_OVERWRITE_IF` (`EINVAL`);
   N:82–89 also permits a caller-supplied SD on replacement by
   `FILE_SUPERSEDE`. D:36–46 and G:19–36 show `OPEN_IF` with a non-null
   creator SD and imply that the existing-file branch succeeds, despite
   O and N rejecting it. Those examples do not resolve the disagreement.

4. **Replacement and status.** O:71 says `SUPERSEDE` removes the inode
   and recommends it for atomic-replace patterns. N:82–89 replaces the
   pathname while preserving old hardlinks and already-open references.
   O:112 claims nonconditional dispositions predict the status; N:176–179
   says an absent-target `FILE_SUPERSEDE` reports `CREATED`, with
   `SUPERSEDED` only for actual replacement. No atomicity guarantee follows
   from this comparison.

5. **Delete-on-close.** O:80 describes deletion on the last fd referencing
   the file. N:112–129 instead specifies final close of one file-description
   lineage, preserved by `dup`, `fork` and `SCM_RIGHTS`; later opens fail
   closed, and only regular files are supported. Generic inode
   last-reference semantics and this no-share lineage boundary differ.

6. **Unverified raw details.** O:88 claims native `AT_EMPTY_PATH` opens
   an empty path against the directory referenced by `dirfd`; N:66–69
   discusses that flag for get/set-security, not native open. O:140–143
   maps `O_CREAT` to `OPEN_IF` with parent `FILE_ADD_FILE`,
   `O_CREAT | O_EXCL` to `CREATE`, and `O_NOFOLLOW` to
   `AT_SYMLINK_NOFOLLOW`. Their exact legacy translation and parent-right
   timing are not established by N/L/D. O:170 attributes legacy creation
   to umask-based defaults plus parent inheritable ACEs; [Inheritance](~peios/security-descriptors/inheritance#the-merge-algorithm)
   describes parent, creator and token SD sources without establishing
   that umask contribution. O:183,185 also lists path-component
   `ENOTDIR` and invalid-disposition `EINVAL`. These remain earlier,
   unverified claims; omission from another reference does not prove
   rejection or support. O:180 distinguishes a failed open access check
   from an unreachable path component; [directory traversal](~peios/advanced-peios/peios-kernel/kacs/facs/use-time#directory-traversal)
   is a separate authorization check.

7. **SDK destination caveats.** D:3 mentions share mode; D:28 describes
   no-follow, write-through and the rest of the `NtCreateFile` option set.
   N:111–120 instead lists two supported create-option bits, reserves all
   others, and says the ABI has no share-mode field. D:26 calls the native
   result a “granted subset,” while N:6–19 distinguishes strict requests
   from maximum-allowed requests. The SDK reference is a programming
   entry point, not evidence that these differences have been reconciled.

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
`CONFIG_STRICT_DEVMEM=y` and `CONFIG_MODULE_SIG_FORCE=y`. The last two,
and the absence of every other MAC LSM and of `CONFIG_BPF_LSM`, are
enforced at build time by `BUILD_BUG_ON` in `pkm_init` (§3.7): a kernel
configured without them does not compile. They were once checked at
initialisation instead, which is no refusal at all -- the LSM framework
answers a failed init with a warning and boots with the hooks
uninstalled, the opposite of what the gate intends (PEI-487). [*abi-notes.build.configs-enforced-at-build]
`CONFIG_SECURITY_SELINUX`, `_APPARMOR`, `_SMACK` and `_TOMOYO` are
additionally refused by Kconfig dependency. `CONFIG_LSM` is never
parsed.

Two further symbols gate large bodies of code:

- `CONFIG_SECURITY_PKM_KUNIT`, which compiles in the test harness and,
  in the signing path, a different and publicly known verification key
  (§3.6). [*abi-notes.build.kunit-test-key]
- `CONFIG_STRATAFS_FS`, without which the copy-up API of §3.9.7 is
  inert. [*abi-notes.build.stratafs-gates-copy-up]
