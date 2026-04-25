---
title: Token Access Rights
---

Tokens are securable objects. Every token has its own Security Descriptor, and accessing a token requires passing an AccessCheck against that SD.

## Obtaining a token file descriptor

**Open directly.** A syscall takes a process identifier (PID or pidfd) and a desired access mask. The kernel finds the target process's primary token, evaluates the caller's token against the target token's SD, and returns a token fd with the granted access mask cached on it. A separate variant opens a thread's impersonation token. Opening another process's token also requires `PROCESS_QUERY_INFORMATION` on the target process's SD.

**Receive via IPC.** A token fd MAY be passed over a Unix socket via SCM_RIGHTS. The recipient's operations are constrained by the access mask cached on the fd at the time it was originally opened.

**Implicit access.** A thread always has implicit access to its own effective token for query operations. This is not a kernel bypass — it is guaranteed by the default token SD, which grants TOKEN_QUERY (plus adjustment rights) to the token's own user SID. The AccessCheck still runs; it simply always succeeds for self-query under the default SD.

## Token-specific access rights

| Right | Value | Grants |
|---|---|---|
| TOKEN_ASSIGN_PRIMARY | 0x0001 | Install as a process's primary token. Also requires `SeAssignPrimaryTokenPrivilege` on the caller's token. |
| TOKEN_DUPLICATE | 0x0002 | Duplicate the token (DuplicateToken) or create a restricted copy (FilterToken). |
| TOKEN_IMPERSONATE | 0x0004 | Install as a thread's impersonation token. |
| TOKEN_QUERY | 0x0008 | Read token information: SIDs, groups, privileges, integrity, claims, source, statistics, elevation type. |
| TOKEN_ADJUST_PRIVILEGES | 0x0020 | Enable, disable, or permanently remove privileges. |
| TOKEN_ADJUST_GROUPS | 0x0040 | Enable or disable groups. |
| TOKEN_ADJUST_DEFAULT | 0x0080 | Change default DACL, owner SID, and primary group SID. |
| TOKEN_ADJUST_INTERACTIVITY_SCOPE | 0x0100 | Change interactivity scope. Also requires `SeTcbPrivilege`. |

Bit 0x0010 (TOKEN_QUERY_SOURCE) is subsumed by TOKEN_QUERY — a holder of TOKEN_QUERY (0x0008) can also query source information. The 0x0010 bit MUST NOT be reused for other purposes (format compatibility with MS-DTYP).

TOKEN_ALL_ACCESS = 0x000F01FF. This is the union of all token-specific rights (0x01FF = bits 0-8, including the reserved TOKEN_QUERY_SOURCE bit 0x0010 for MS-DTYP format compatibility) plus STANDARD_RIGHTS_REQUIRED (DELETE | READ_CONTROL | WRITE_DAC | WRITE_OWNER = 0x000F0000). The named rights OR to 0x01EF; the reserved bit adds 0x0010 to reach 0x01FF.

## Generic mapping

| Generic right | Maps to |
|---|---|
| GENERIC_READ | TOKEN_QUERY \| READ_CONTROL |
| GENERIC_WRITE | TOKEN_ADJUST_PRIVILEGES \| TOKEN_ADJUST_GROUPS \| TOKEN_ADJUST_DEFAULT \| WRITE_DAC |
| GENERIC_EXECUTE | TOKEN_IMPERSONATE |
| GENERIC_ALL | TOKEN_ALL_ACCESS (0x000F01FF) |

## Standard rights

| Right | Grants |
|---|---|
| READ_CONTROL | Read the token's own SD. |
| WRITE_DAC | Modify the token's DACL. |
| WRITE_OWNER | Change the token's owner. |
| DELETE | No practical effect for tokens. Present for standard rights uniformity. |

## Default token SD

When a token is created, it receives a default SD:

- **Owner:** the creating process's user SID.
- **DACL:**
  - ALLOW the token's own user SID: TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT.
  - ALLOW the creator: TOKEN_ALL_ACCESS.
  - ALLOW SYSTEM (`S-1-5-18`): TOKEN_ALL_ACCESS.

Self-access is limited to adjustment operations that cannot escalate. TOKEN_DUPLICATE, TOKEN_IMPERSONATE, and WRITE_DAC are not granted to the token's subject by default.

## Access check model

The check-at-open model applies to tokens exactly as it does to files: AccessCheck runs once when the token fd is obtained, the granted access mask is cached on the fd, and subsequent operations verify the cached mask. No per-operation re-evaluation.
