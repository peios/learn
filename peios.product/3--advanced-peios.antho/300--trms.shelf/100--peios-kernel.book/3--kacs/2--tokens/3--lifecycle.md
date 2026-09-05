---
title: Token Lifecycle
description: How tokens follow a process through fork, clone and exec — NEW_PROCESS_MIN, self-installation, bootstrap tokens and external tokens.
---

## Fork and clone

Every process and thread creation path goes through `clone()`, and
KACS branches on `CLONE_THREAD`.

**Without `CLONE_THREAD`** — fork or vfork — a new process is created
and the child receives an independent deep copy of the parent's
primary token. [*token.fork.independent-copy] If the parent is impersonating, the impersonation token
is not inherited: the child's effective credential is set from
`real_cred`. [*token.fork.impersonation-not-inherited] After the fork, mutations to either token are invisible
to the other. [*token.fork.mutations-invisible-after]

**With `CLONE_THREAD`** a new thread is created. Threads share the
parent's `real_cred` by reference and therefore share one primary
token object, so a privilege adjustment on it is visible to every
thread. [*token.thread.shared-primary] Each thread keeps independent impersonation state through its
own `cred`. [*token.thread.independent-impersonation] If the cloning thread is impersonating at the moment of
the clone, the impersonation token does not become the new thread's
primary or effective identity — the new thread starts with the shared
primary token as both, and may impersonate independently later. [*token.thread.clone-starts-on-primary]

## Exec

The primary token survives `execve()` unchanged, with the single
exception of `NEW_PROCESS_MIN` below. [*token.exec.primary-survives] If the calling thread is
impersonating, impersonation is reverted before the new program runs;
a new program always starts with the primary token as its effective
identity. [*token.exec.reverts-impersonation]

Token assignment for services happens between fork and exec: peinit
forks, installs the service's token on the child, and the child then
execs the service binary.

### NEW_PROCESS_MIN [*token.new-process-min]

When a token's `mandatory_policy` includes `NEW_PROCESS_MIN`, the
kernel replaces the primary token at exec time if the executable
carries an explicit, lower integrity label.

1. The executable's integrity label is read from the mandatory label
   ACE in its descriptor's SACL. A file with no label — no SACL, or no
   non-inherit-only mandatory label ACE — is **unlabelled**, and the
   token survives exec unchanged. [*token.new-process-min.unlabelled-unchanged] This is deliberately not the
   access-check rule, under which an unlabelled *object* counts as
   Medium (§3.8.3): an image that labels nothing would otherwise demote
   every process on it, PID 1 first, to Medium — which is exactly what
   happened before PEI-530, leaving the TCB below every High-integrity
   user and unable to convey their identity.
2. If the file's level is lower than the token's, a new token is
   created following DuplicateToken semantics — new `token_id`, new
   `token_guid`, `modified_id` initialised to the new `token_id`,
   `elevation_type` reset to Default — with `integrity_level` set to
   the file's label. Every other field — the impersonation level
   included — is copied from the source, and the original token is
   dropped. [*token.new-process-min.lowers-to-file-label]
3. If the file's level is greater than or equal to the token's,
   nothing happens and the token survives exec unchanged. [*token.new-process-min.higher-label-unchanged]

The mechanism only ever lowers integrity, so a child's level is always
at most its parent's, and only to a level the image itself claims. The
flag itself is immutable on the token, which is what prevents a process
from opting out before exec.

## Self-installing a primary token

`KACS_IOC_INSTALL` commits a new primary token on the calling process.
The operation is process-wide: the kernel replaces the primary token
for the entire thread group, not just the calling thread. [*token.install.process-wide]

The handle has to carry `TOKEN_ASSIGN_PRIMARY`, the token has to be a
primary token, and the caller's *real* token has to hold
`SeAssignPrimaryTokenPrivilege` enabled — an impersonating thread's
effective token does not satisfy the gate, and the privilege is marked
used on success. [*token.install.gates] Unless that real token also
holds `SeTcbPrivilege` enabled, the token being installed has to carry
the same user SID and the same LogonSession as the caller's, or the
call fails with `EPERM`; this is what stops a non-TCB holder of
`SeAssignPrimaryTokenPrivilege` from installing an arbitrary
higher-privilege token on itself, and `SeTcbPrivilege` bypassing it is
how peinit installs service tokens with a different user SID and
LogonSession. [*token.install.same-user-same-session-unless-tcb]

A thread that is not impersonating switches both `real_cred` and
`cred` to the new primary token. A thread that is impersonating has
only `real_cred` replaced, and its active impersonation stays in
`cred` until it reverts or execs — so reverting after an install
restores the thread to the *new* primary token, not the old one. [*token.install.impersonating-thread-keeps-cred]

The calling thread installs immediately. Sibling threads converge in
their own context through queued in-kernel credential work, with no
atomic all-threads-at-once swap: during a brief transition window some
siblings may still observe the old primary token until they run their
queued work. [*token.install.siblings-converge-asynchronously] No completion barrier is exposed to the caller.

If the installed token's user SID differs from the outgoing primary
token's, the process security descriptor is regenerated from the
default template for the new token. Otherwise the existing process
descriptor is preserved. [*token.install.process-sd-regenerated-on-sid-change]

## Bootstrap tokens

Two tokens are created by PKM during kernel initialisation, before any
userspace process exists. Neither involves a syscall — the kernel
allocates the objects directly.

The **SYSTEM token** is hardcoded with user SID `S-1-5-18` (Local
System); groups `S-1-5-32-544` (BUILTIN\Administrators), `S-1-1-0`
(Everyone), `S-1-5-11` (Authenticated Users) and other well-known
SIDs; every defined privilege present and enabled; integrity level
System; token type Primary; impersonation level Delegation, the top of
the ratchet; elevation type Default; token source `PeiosKrn`;
projected UID 0; and `auth_id` set to `SYSTEM_LUID`. It is assigned to
the kernel's init task and inherited by PID 1 at exec. [*token.bootstrap.system-token]

The **Anonymous token** is a global singleton with user SID `S-1-5-7`;
Everyone (`S-1-1-0`) as its only group; no privileges; integrity level
Untrusted; logon type Network; token type Impersonation; impersonation
level Anonymous; elevation type Default; token source `PeiosKrn`; and
`auth_id` set to `ANONYMOUS_LOGON_LUID`. It is effectively immutable,
having no privileges and no groups to adjust. [*token.bootstrap.anonymous-token] A peer token captured
at Anonymous level references this global object, whereas
`KACS_IOC_DUPLICATE` targeting Anonymous level creates a fresh
independent token of the same shape, because the DuplicateToken
contract requires a new object. [*token.bootstrap.anonymous-singleton-vs-duplicate]

| LUID | Value | Description |
|---|---|---|
| `SYSTEM_LUID` | 999 (0x3E7) | The SYSTEM LogonSession, created at kernel init. |
| `ANONYMOUS_LOGON_LUID` | 998 (0x3E6) | The Anonymous LogonSession, created at kernel init for Anonymous impersonation tokens. |

LogonSessions created dynamically by authd receive auto-generated
LUIDs starting at 1000; 999 and 998 are never assigned dynamically. [*token.bootstrap.reserved-luids]

The SYSTEM token carries `SeBackupPrivilege` and `SeRestorePrivilege`
present and enabled at boot. [*token.bootstrap.system-backup-restore-present] FACS passes backup and restore intent
flags into AccessCheck, which grants read and write regardless of file
DACLs — subject still to PIP. [*token.bootstrap.backup-restore-intent-bypasses-dacl] Once peinit has launched the TCB
services and early boot is complete, it disables these on child
service tokens through FilterToken.

## External token replacement

A privileged process being able to replace the primary token on
another running process — peinit downgrading a pre-authd service from
SYSTEM to a purpose-built token, for instance — is designed but **not
built**. Nothing in the kernel implements it today. [*token.external-replacement-not-built]

The design uses `task_work_add()` to queue a credential swap on each
task in the target thread group, each task executing the swap in its
own context to preserve RCU safety, with an impersonating thread
having only `real_cred` replaced and its impersonation left intact.
The gates would be `SeAssignPrimaryTokenPrivilege` on the caller's
real token, `TOKEN_ASSIGN_PRIMARY` (0x0001) on the token fd,
`PROCESS_SET_INFORMATION` on the target process's descriptor, and two
constraints — the new token's user SID matching the target's current
one, and the new token belonging to the same LogonSession — both
bypassed by `SeTcbPrivilege`. The process descriptor gate puts the
target's owner in control of who can change its identity, while the
SID and LogonSession constraints stop a non-TCB holder of
`SeAssignPrimaryTokenPrivilege` assigning an arbitrary token to a
process it can reach. `SeTcbPrivilege` bypassing both is how peinit
would assign tokens with different user SIDs and LogonSessions to
child services. Per-thread queuing would leave a brief window with
some threads on the new token and some on the old, which is acceptable
only because replacement is always a downgrade.

In its absence, the mitigation for pre-authd services is privilege
removal: peinit uses FilterToken to copy the SYSTEM token with the
dangerous privileges permanently deleted and assigns that filtered
token to the service at launch. The service keeps the SYSTEM SID but
permanently lacks the ability to exercise those privileges.
