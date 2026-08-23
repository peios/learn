---
title: Token Access Rights
description: Tokens are securable objects — obtaining a token file descriptor, the token-specific rights, the generic mapping and the default descriptor.
---

Tokens are securable objects: each has its own security descriptor,
and reaching a token means passing an AccessCheck against it.

## Obtaining a token file descriptor

**Opening directly.** A syscall takes a pidfd — not a raw PID — and a
desired access mask. The kernel finds the target's
primary token, evaluates the caller's token against that token's
descriptor, and returns a token fd with the granted mask cached on it.
A separate variant opens a thread's impersonation token. Opening
another process's token additionally requires
`PROCESS_QUERY_INFORMATION` on the target process's descriptor.

`kacs_open_peer_token` is the exception: it takes no desired-access
mask, and the fd it returns always carries the fixed rights
`TOKEN_QUERY | TOKEN_IMPERSONATE`.

**Receiving over IPC.** A token fd can be passed over a Unix socket
with `SCM_RIGHTS`. What the recipient may do is bounded by the mask
cached on the fd when it was originally opened, not by the recipient's
own identity.

**Implicit self-access.** A thread has implicit access to its own
effective token for query operations, but this is not a kernel bypass.
It follows from the default token descriptor, which grants
`TOKEN_QUERY` and the adjustment rights to the token's own user SID.
The AccessCheck still runs; it simply succeeds while the descriptor
continues to grant the right. Explicitly mutating a token's own
descriptor later can revoke self-query by removing that grant.

## Token-specific rights

| Right | Value | Grants |
|---|---|---|
| `TOKEN_ASSIGN_PRIMARY` | 0x0001 | Install as a process's primary token. Also requires `SeAssignPrimaryTokenPrivilege` on the caller's token. |
| `TOKEN_DUPLICATE` | 0x0002 | Duplicate the token, or create a restricted copy with FilterToken. |
| `TOKEN_IMPERSONATE` | 0x0004 | Install as a thread's impersonation token. |
| `TOKEN_QUERY` | 0x0008 | Read token information: SIDs, groups, privileges, integrity, claims, source, statistics, elevation type. |
| `TOKEN_ADJUST_PRIVILEGES` | 0x0020 | Enable, disable, or permanently remove privileges. |
| `TOKEN_ADJUST_GROUPS` | 0x0040 | Enable or disable groups. |
| `TOKEN_ADJUST_DEFAULT` | 0x0080 | Change the default DACL, owner SID, and primary group SID. |
| `TOKEN_ADJUST_INTERACTIVITY_SCOPE` | 0x0100 | Change the interactivity scope. Also requires `SeTcbPrivilege`. |

Bit 0x0010, `TOKEN_QUERY_SOURCE`, is subsumed by `TOKEN_QUERY`: a
holder of 0x0008 can query source information too. The bit is not
reused for anything else, for format compatibility with MS-DTYP.

`TOKEN_ALL_ACCESS` is 0x000F01FF — the union of the token-specific
rights with `STANDARD_RIGHTS_REQUIRED`
(`DELETE | READ_CONTROL | WRITE_DAC | WRITE_OWNER`, 0x000F0000). The
named rights alone OR to 0x01EF; the reserved `TOKEN_QUERY_SOURCE` bit
adds 0x0010 to reach 0x01FF.

## Generic mapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `TOKEN_QUERY \| READ_CONTROL` |
| `GENERIC_WRITE` | `TOKEN_ADJUST_PRIVILEGES \| TOKEN_ADJUST_GROUPS \| TOKEN_ADJUST_DEFAULT \| WRITE_DAC` |
| `GENERIC_EXECUTE` | `TOKEN_IMPERSONATE` |
| `GENERIC_ALL` | `TOKEN_ALL_ACCESS` (0x000F01FF) |

## Standard rights

`READ_CONTROL` reads the token's own descriptor, `WRITE_DAC` modifies
its DACL, and `WRITE_OWNER` changes its owner. `DELETE` has no
practical effect on a token and is present only for uniformity across
standard rights.

## The default token descriptor

A newly created token receives a descriptor owned by the creating
process's user SID, with a DACL granting:

- the token's own user SID `TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES |
  TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT`;
- the creator `TOKEN_ALL_ACCESS`;
- SYSTEM (`S-1-5-18`) `TOKEN_ALL_ACCESS`.

Self-access is deliberately limited to the adjustment operations that
cannot escalate. `TOKEN_DUPLICATE`, `TOKEN_IMPERSONATE`, and
`WRITE_DAC` are not granted to the token's own subject.

That limit needs protecting in the case where the creator and the
token's own user SID are the same, which would otherwise hand the
subject `TOKEN_ALL_ACCESS` through the creator ACE. When the two SIDs
are identical the creator ACE is omitted — and the descriptor also
gains a non-inherit-only `OWNER RIGHTS` ACE suppressing the owner's
implicit `READ_CONTROL | WRITE_DAC` grant while preserving
`READ_CONTROL`. Without it, owner-implicit `WRITE_DAC` would let the
subject rewrite its own DACL and reintroduce exactly the escalation
that omitting the creator ACE was meant to close.

## Check-at-open

The check-at-open model applies to tokens exactly as it does to files,
for the token-specific rights. AccessCheck runs once, when the token
fd is obtained; the granted mask is cached on the fd; and each of the
token ioctls verifies against that cached mask with no re-evaluation.

The standard rights are the exception. Reading and writing a token's
own descriptor passes no cached mask at all and runs a **live**
AccessCheck on every call, so `READ_CONTROL`, `WRITE_DAC` and
`WRITE_OWNER` are re-evaluated per operation rather than snapshotted
at open. A descriptor change therefore takes effect immediately for
those three rights, while already-opened handles keep their cached
token-specific rights.
