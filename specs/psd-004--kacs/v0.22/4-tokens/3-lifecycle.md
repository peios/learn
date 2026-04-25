---
title: Token Lifecycle
---

## Fork and clone

All process and thread creation paths go through `clone()`. KACS branches on the `CLONE_THREAD` flag.

### Clone without CLONE_THREAD (fork, vfork)

New process. The child MUST receive an independent deep copy of the parent's primary token. If the parent is impersonating, the impersonation token MUST NOT be inherited — the child's effective credential is set from `real_cred`.

After fork, mutations to either token (parent or child) are invisible to the other.

### Clone with CLONE_THREAD

New thread. Threads share the parent's `real_cred` (reference-counted), and therefore share the same primary token object. Privilege adjustments on the primary token are visible to all threads. Each thread maintains independent impersonation state via its own `cred`.

### Exec

The primary token survives `execve()` unchanged, with one exception: the NEW_PROCESS_MIN mechanism (below).

If the calling thread is impersonating, impersonation MUST be reverted before the new program runs. The new program always starts with the primary token as its effective identity.

Token assignment for services happens between fork and exec: peinit forks, installs the service's token on the child, then the child execs the service binary.

### NEW_PROCESS_MIN

If the token's `mandatory_policy` includes NEW_PROCESS_MIN, the kernel MUST replace the child's primary token at exec time when the executable has a lower integrity label:

1. Read the executable file's integrity label from its SD (the mandatory label ACE in the SACL). If the file has no label, use the default (Medium).
2. If the file's integrity level is lower than the token's integrity level, create a new token following DuplicateToken semantics (new `token_id`, `modified_id` initialized to the new `token_id`, `elevation_type` reset to Default) with `integrity_level` set to the file's label. All other fields are copied from the source. The original token is dropped.
3. If the file's integrity level is greater than or equal to the token's integrity level, no action — the token survives exec unchanged.

NEW_PROCESS_MIN can only lower integrity, never raise it. The child's integrity level is always less than or equal to the parent's. The flag is immutable on the token.

## Bootstrap

The SYSTEM token (`S-1-5-18`) is created by PKM during kernel initialization, before any userspace process exists. It is hardcoded:

- User SID: `S-1-5-18` (Local System)
- Groups: `S-1-5-32-544` (BUILTIN\Administrators), `S-1-1-0` (Everyone), `S-1-5-11` (Authenticated Users), and other well-known SIDs
- Privileges: all defined privileges, present and enabled
- Integrity level: System
- Token type: Primary
- Elevation type: Default (no linked token)
- Token source: `PeiosKrn`
- Projected UID: 0
- auth_id: SYSTEM_LUID (0x000003E7 = 999)

The SYSTEM token is assigned to the kernel's init task and inherited by PID 1 on exec. No syscall is involved — the kernel allocates the token object directly during initialization.

The Anonymous token (`S-1-5-7`) is also created by PKM during kernel initialization. It is a global singleton:

- User SID: `S-1-5-7` (Anonymous)
- Groups: none (Everyone included only if the system-wide Anonymous-in-Everyone policy is set — see Impersonation Lifecycle)
- Privileges: none
- Integrity level: Untrusted
- Token type: Impersonation
- Impersonation level: Anonymous
- Elevation type: Default
- Token source: `PeiosKrn`
- auth_id: ANONYMOUS_LOGON_LUID (0x000003E6 = 998)

The Anonymous token is effectively immutable (no privileges to adjust, no groups to adjust). `kacs_impersonate_peer` at Anonymous level references this global token. `KACS_IOC_DUPLICATE` with target level=Anonymous creates a fresh independent token matching this shape (the DuplicateToken contract requires a new token object).

### Well-known LogonSession LUIDs

| LUID | Value | Description |
|---|---|---|
| SYSTEM_LUID | 999 (0x3E7) | The SYSTEM LogonSession. Created at kernel init. |
| ANONYMOUS_LOGON_LUID | 998 (0x3E6) | The Anonymous LogonSession. Created at kernel init for Anonymous impersonation tokens. |

Dynamically created LogonSessions (by authd via `kacs_create_logon_session`) receive auto-generated LUIDs starting at 1000. The kernel MUST NOT assign 999 or 998 to dynamic LogonSessions.

> [!INFORMATIVE]
> The SYSTEM token carries SeBackupPrivilege and SeRestorePrivilege (present and enabled at boot). FACS passes backup/restore intent flags to AccessCheck, which grants read and write access regardless of file DACLs — subject to PIP enforcement. Once peinit has launched TCB services and early boot is complete, peinit disables these privileges on child service tokens via FilterToken.

## External token replacement

> [!WARNING]
> External token replacement is not implemented in v0.20. This section defines the intended behaviour for a future release.

A privileged process (peinit) MAY replace the primary token on a running process — for example, downgrading a pre-authd service from SYSTEM to a purpose-built token.

The mechanism uses `task_work_add()` to queue a credential swap on each task in the target thread group. Each task executes the swap in its own context, preserving RCU safety. If a thread is impersonating, the replacement affects `real_cred` (primary token) only — the impersonation state is left intact.

### Requirements

- SeAssignPrimaryTokenPrivilege on the caller's real token.
- TOKEN_ASSIGN_PRIMARY (0x0001) on the token fd.
- PROCESS_SET_INFORMATION on the target process's SD.
- The new token's user SID MUST match the target's current primary token's user SID, unless the caller has SeTcbPrivilege.
- The new token MUST belong to the same LogonSession (matching `auth_id`) as the target's current primary token, unless the caller has SeTcbPrivilege.

The process SD gate ensures the target process's owner controls who can change its identity. The SID and LogonSession constraints prevent a non-TCB holder of SeAssignPrimaryTokenPrivilege from assigning an arbitrary token to a process it can reach. SeTcbPrivilege bypasses the SID and LogonSession constraints — this is how peinit assigns tokens with different user SIDs and LogonSessions to child services.

> [!INFORMATIVE]
> The per-thread queuing creates a brief transition window where some threads have the new token while others still have the old one. This is acceptable because replacement is always a privilege downgrade. There is no completion barrier — the caller cannot determine when all threads have executed the swap.

> [!INFORMATIVE]
> Until external token replacement is implemented, the mitigation for pre-authd services is privilege removal: peinit uses FilterToken to create a copy of the SYSTEM token with dangerous privileges permanently deleted, and assigns this filtered token to the service at launch. The service retains the SYSTEM SID but permanently lacks the ability to exercise privileged operations.
