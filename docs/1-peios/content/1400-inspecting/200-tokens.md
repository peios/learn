---
title: Inspecting tokens
type: concept
description: A token's contents are read via KACS_IOC_QUERY on a token fd. Token fds come from kacs_open_self_token, /proc/<pid>/token, /sys/kernel/security/kacs/self, and a few other paths. Each query is a numbered class returning structured data. This page covers the query mechanism, the catalog of classes, and the two-call pattern for variable-length data.
related:
  - peios/inspecting/overview
  - peios/inspecting/sessions
  - peios/inspecting/processes
  - peios/tokens/overview
  - peios/tokens/token-types
---

A token's fields are read through the `KACS_IOC_QUERY` ioctl on a token fd. The ioctl takes a query class — a small integer naming what to return — and returns the corresponding data structured per that class. There are 24 defined classes covering everything from "the user SID" to "the full set of resource attribute claims".

This page covers how to obtain a token fd, the query ioctl mechanics, the two-call pattern for queries with variable-length output, and an overview of the class catalog.

## Obtaining a token fd

Token fds come from a handful of syscalls and pseudo-files:

| Source | Returns | Access check |
|---|---|---|
| `kacs_open_self_token` | The calling thread's effective token (or primary, with `KACS_REAL_TOKEN` flag) | None — always succeeds |
| `kacs_open_process_token(pidfd)` | A target process's primary token | `PROCESS_QUERY_INFORMATION` + PIP dominance + token SD rights |
| `kacs_open_thread_token(tid)` | A specific thread's effective token | Same as above |
| `kacs_open_peer_token(sock_fd)` | The peer's captured identity on a connected Unix socket | None beyond the connection itself |
| `/proc/<pid>/token` | The primary token of process `<pid>` | `PROCESS_QUERY_INFORMATION` + PIP dominance |
| `/proc/<pid>/task/<tid>/token` | The effective token of thread `<tid>` in process `<pid>` | Same |
| `/sys/kernel/security/kacs/self` | The calling thread's effective token | None — always readable |

The fds carry an access mask. The mask is what the kernel granted at open time and what the subsequent ioctl will check against. A fd opened with `TOKEN_QUERY` cannot be used to install or duplicate the token; the ioctl will see the request as exceeding the fd's mask and refuse.

The pseudo-files under `/proc` and `/sys/kernel/security/kacs/` return read-only fds — they carry `TOKEN_QUERY` and nothing else. To get a fd with more access you need one of the syscalls.

## KACS_IOC_QUERY

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

For classes with a fixed-size response (most of them), a single call with a buffer of the known size works in one go. The two-call pattern is needed only for classes whose response size depends on the token's contents (the groups class, the privileges class, the claims classes).

The ioctl is **idempotent** — multiple queries for the same class produce the same result as long as the token has not been modified. Tokens carry a `modified_id` counter that increments on adjustment; if a query is part of a pipeline that depends on consistency across multiple queries, the `modified_id` can be queried first to detect mid-pipeline changes.

## Query class catalog

There are 24 defined query classes. Each returns a structured payload defined for that class. The most commonly used:

| Class | Returns |
|---|---|
| `TokenUser` | The token's `user_sid` and its attributes. |
| `TokenGroups` | The `groups` array — every group SID with its attributes. Variable length. |
| `TokenPrivileges` | The privilege bitmask — present, enabled, used, enabled_by_default. |
| `TokenOwner` | The default owner SID. |
| `TokenPrimaryGroup` | The default primary group SID. |
| `TokenDefaultDacl` | The token's default DACL. Variable length. |
| `TokenSource` | The source name and source-LUID identifying who minted the token. |
| `TokenType` | Primary or Impersonation. |
| `TokenImpersonationLevel` | Anonymous / Identification / Impersonation / Delegation (only meaningful for Impersonation tokens). |
| `TokenStatistics` | `token_id`, `auth_id`, modified_id, creation timestamp, expiry, dynamic charge, and so on. |
| `TokenRestrictedSids` | The `restricted_sids` array. Variable length. |
| `TokenSessionId` | The interactive session ID. |
| `TokenGroupsAndPrivileges` | A combined version of TokenGroups and TokenPrivileges for performance. Variable length. |
| `TokenSessionReference` | The session reference (a token holds onto its session via this; less commonly inspected). |
| `TokenSandBoxInert` | (Reserved / future use.) |
| `TokenAuditPolicy` | The token's `audit_policy` bitmask. |
| `TokenOrigin` | The originating session LUID for derived tokens. |
| `TokenElevationType` | Default / Full / Limited. |
| `TokenLinkedToken` | If part of a linked pair, the partner. (Returns a token fd; subject to additional access rules.) |
| `TokenElevation` | A simplified "is this elevated" query. |
| `TokenHasRestrictions` | A boolean: is this a restricted token? |
| `TokenIntegrityLevel` | The integrity SID. |
| `TokenUiAccess` | The UI-access flag. (Reserved.) |
| `TokenMandatoryPolicy` | The `mandatory_policy` flags (NO_WRITE_UP, NEW_PROCESS_MIN). |

This is the full v0.20 list. Each class's exact byte-level payload format is in the [Wire formats reference](~peios/wire-formats-reference/overview); this page covers what each class is for.

## Patterns by use case

A handful of patterns come up repeatedly:

**"Who is this thread acting as?"** Open the thread's effective token (`/proc/<pid>/task/<tid>/token` or `kacs_open_self_token`). Query `TokenUser` to get the principal SID. Optionally query `TokenImpersonationLevel` to see if this is an impersonation token, and what level.

**"What rights does this token have on this object?"** This is not a query — you call AccessCheck with the token, the object's SD, and the access mask you want to test. Querying the token alone does not tell you the answer; the rights depend on the SD too.

**"Which session does this token belong to?"** Query `TokenStatistics` to get `auth_id`. Look up that ID in `/sys/kernel/security/kacs/sessions` for the session's details.

**"Is this token elevated?"** Query `TokenElevationType`. If Full, this token is the elevated half of a linked pair. If Default, it is not part of a pair. If Limited, it is the non-elevated half — the elevated counterpart is reachable via `KACS_IOC_GET_LINKED_TOKEN`.

**"What privileges can this token actually exercise?"** Query `TokenPrivileges` and inspect both the present and enabled bitmasks. A privilege is exercisable if it is both present and enabled. A privilege that is present but disabled can be enabled via AdjustPrivileges; a privilege that is absent cannot.

**"Has this token been adjusted since I last looked?"** Query `TokenStatistics`. The `modified_id` field is a counter that increments on every adjustment. If it has changed since your last query, the token has been adjusted.

## What query classes do not let you do

A few clarifications:

- **You cannot modify a token through a query class.** Queries are read-only. Modification goes through AdjustPrivileges, AdjustGroups, AdjustDefault, or `kacs_set_sd`.
- **You cannot enumerate every token on the system.** There is no "list all tokens" call. You can walk `/proc/*/token` to find tokens belonging to currently-running processes, but tokens held only by file descriptors with no associated running process are not enumerable.
- **You cannot read tokens you do not have authority for.** A token fd with only `TOKEN_QUERY` lets you query, but the fd had to be opened with appropriate authority. The query ioctl does not bypass the access checks at open time.
- **You cannot query classes that are reserved.** A class number reserved for future use (some of the higher-numbered slots) returns `-EINVAL`. Only the defined classes are valid.

## Reading from the shell

For a sysadmin debugging at a terminal, the [`token`](~peios/tokens/token-command) command is the utility that wraps this ioctl. It handles the two-call pattern, decodes the binary payloads, and renders the results as readable text — so the query classes above become `token` subcommands rather than raw ioctl calls.

For programmatic use, the ioctl is what you call directly. Language bindings (the C SDK, the Python wrapper) provide ergonomic wrappers but ultimately call the same ioctl.

The pseudo-file approach — `/proc/<pid>/token`, `/sys/kernel/security/kacs/self` — gives you the token fd; the actual query still goes through the ioctl. Pseudo-files are just a convenient way to acquire the fd from the shell.
