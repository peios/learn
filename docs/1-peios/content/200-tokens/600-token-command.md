---
title: The token command
type: reference
description: token is the command-line tool for inspecting and manipulating tokens directly — reading a token's contents, adjusting it, duplicating and restricting it, and driving impersonation.
related:
  - peios/tokens/overview
  - peios/tokens/token-types
  - peios/tokens/restricted-tokens
  - peios/impersonation/overview
  - peios/inspecting/tokens
---

`token` is the command-line tool for working with **tokens** directly. It reads a token's contents, adjusts it, produces derived tokens, and drives impersonation — the low-level operations this topic describes, exposed at a shell.

```
token subcommand [target] [arguments]
```

```
$ token                       # one-line summary of your own token
$ token show --all             # every field of your own token
$ token privs --pid 4821       # the privileges on process 4821's token
```

`token` is a direct, **debug-level** tool. Day to day you do not inspect tokens by hand — the system does. `token` is for diagnosing an access problem, for understanding what identity a process is really running under, and for building and testing identity setups. Run with no subcommand, it prints a one-line summary of your own token.

## Choosing which token

Almost every subcommand operates on a token, and these flags choose which one. With none, the target is your own.

| Flag | Target |
|---|---|
| `--self` | Your own token. The default. |
| `--real` | Your **primary** token specifically, rather than the effective one — relevant when your thread is impersonating. |
| `--pid PID` | The primary token of process `PID`. |
| `--tid TID` | The impersonation token of thread `TID` (used with `--pid`). |
| `--peer SOCK_FD` | The peer's captured token on a connected socket — see [Peer tokens](~peios/impersonation/peer-tokens). |

Reading another process's token is itself access-controlled: it succeeds only with the right authority over that process.

## Inspecting a token

### `show`

`token show` prints a token's contents. It is the default — bare `token` is `token show --short`.

| Flag | Effect |
|---|---|
| `--short` | A one-line summary. |
| `--all` | Every query class — the fullest dump. |

### Field accessors

Each of these prints one part of a token, for when you want just that piece:

| Subcommand | Prints |
|---|---|
| `user` | The user SID — who the token is. |
| `owner` | The default owner SID. |
| `group` | The primary group SID. |
| `groups` | The group list. |
| `privs` | The privileges, with their enabled state. |
| `caps` | The capabilities. |
| `claims` | The user and device claims. |
| `integrity` | The integrity level. |
| `logon` | The logon type and logon SID. |
| `source` | What minted the token. |
| `origin` | The originating session for a derived token. |
| `stats` | Token statistics — IDs, timestamps, the modification counter. |
| `default-dacl` | The token's default DACL. |

### `query`

`token query CLASS` performs a raw read of a single named token-info class and prints the result as JSON — the lowest-level inspection route, for tooling.

## Changing a token

### `adjust`

`token adjust` mutates a token in place:

| Form | Changes |
|---|---|
| `adjust privs NAME=STATE …` | Enable, disable, or remove privileges. `STATE` is `enabled`, `disabled`, or `removed`. |
| `adjust groups IDX=STATE …` | Enable or disable groups by their list index. |
| `adjust default --dacl SDDL` | Replace the token's default DACL. Also `--owner-idx` / `--group-idx`. |
| `adjust session ID` | Replace the token's session id. |

### `restrict`

`token restrict` produces a [restricted token](~peios/tokens/restricted-tokens) — a more limited variant of a token.

| Flag | Effect |
|---|---|
| `--drop-privs MASK\|NAMES` | Privileges to drop. |
| `--deny IDX,…` | Group indices to mark deny-only. |
| `--restrict SID,…` | The restricting SIDs to apply. |

### `duplicate`

`token duplicate` (alias `dup`) copies a token, optionally changing its `--type` (primary or impersonation), its impersonation `--level`, or its `--access` mask.

### `link` and `linked`

`token link` joins two tokens as an elevation pair — a full token and its filtered counterpart — given their file descriptors and a session id. `token linked` shows a token's elevation-linked counterpart, if it has one. See [Elevation](~peios/tokens/elevation).

## Impersonation

| Subcommand | Effect |
|---|---|
| `impersonate` | Begin impersonating the target token on the calling thread. With a trailing `-- command …`, run that command under the impersonating token. |
| `revert` | Drop any active impersonation on the calling thread. |

See [Impersonation](~peios/impersonation/overview) for the model these drive.

## Creating tokens

| Subcommand | Effect |
|---|---|
| `create SPEC` | Create a token from a binary token-spec (`SPEC` is a file, or `-` for standard input). |
| `install SPEC` | Create a token from a spec and install it as the caller's primary token. |

Creating and installing tokens is a privileged operation, reserved for the components that legitimately mint identity.

## Output options

| Flag | Effect |
|---|---|
| `--raw` | Render SIDs in raw `S-1-…` form only. |
| `--label` | Render SIDs as their labels where known, falling back to raw. |
| `--json` | Emit JSON instead of human-readable output. |

## `token` and the inspection surfaces

`token` is the convenient front-end. Underneath, it reads the same kernel surfaces and rules described in [Inspecting tokens](~peios/inspecting/tokens) — that page covers the query mechanism, the access rules for reading another process's token, and what cannot be inspected.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded. |
| `1` | A usage error. |
| non-zero | The operation failed — no such target, an access denial, or a bad spec. |
