---
title: LogonSessions and Revocation
description: The LUID-identified object every token references — how sessions are created, how they expire, and how revocation propagates.
---

## LogonSessions

A LogonSession is a lightweight kernel object identified by a LUID,
carried on tokens as `auth_id`. Every token references one.

authd creates a LogonSession through a KACS syscall at authentication
time, before creating the token. The object holds the LogonSession ID,
the logon type (Interactive, Network, Service, and so on), the user
SID, the authentication package name such as `Kerberos` or
`Negotiate`, and a creation timestamp. The logon SID, `S-1-5-5-X-Y`,
is derived from the LogonSession ID. Several tokens may share one
session — linked pairs, and tokens derived by duplication.

When the last token referencing a session is freed, the kernel
destroys the session object and emits a `logon-session-destroyed`
event through KMES. authd subscribes to those events and uses them to
clean up associated credentials such as cached Kerberos tickets.

There is one rollback path for the case where authd creates a session
but no token ever becomes live for it:
`kacs_destroy_empty_logon_session`, which requires `SeTcbPrivilege`
and succeeds only when the session exists, has zero live tokens, has
no linked-token state, and has no other in-flight kernel references.
On success it destroys the object and emits the same
`logon-session-destroyed` event as normal cleanup. A nonexistent
session fails with `-ENOENT`; one with any live token, linked-token
state, or in-flight reference fails with `-EBUSY`.

A second enumeration surface exists alongside `/proc`:
`/sys/kernel/security/kacs/sessions` lists every live session, one
line each, giving the session ID, user SID, logon type, authentication
package, and creation time. Reading it is access-checked against a
synthetic descriptor granting read to SYSTEM and the creator, and is
PIP-checked.

AccessCheck never consults `auth_id`, and the logon SID influences a
decision only because it is materialised as an ordinary group SID on
the token. Two enforcement decisions elsewhere in the kernel do read
session state, though: installing a primary token denies a non-TCB
caller whose target token belongs to a different LogonSession, and the
`CAP_SYS_BOOT` mapping selects between `SeShutdownPrivilege` and
`SeRemoteShutdownPrivilege` by inspecting the session's logon type. `interactivity_scope` is
metadata in the same way: the kernel stores it and returns it on
query, and no kernel security mechanism evaluates it.

## Expiration

The `expiration` field carries a timestamp, and AccessCheck does not
enforce it. It is informational.

Token lifetime is governed by reference counting instead: a token
exists as long as at least one reference — a process credential or an
open file descriptor — exists.

## Revocation

KACS has no token revocation primitive. There is no "invalidate token
X" syscall, and no syscall destroys a LogonSession while tokens still
reference it. `kacs_destroy_empty_logon_session` is only authd's
rollback for a session that never acquired live tokens.

Terminating a LogonSession is therefore userspace coordination:

1. authd decides a session has to end — an admin request, a security
   incident, an account deletion, or a user logging off.
2. authd enumerates processes whose tokens carry the target `auth_id`
   or `interactivity_scope` by walking `/proc/*/token`, opening each
   node's query-only inspection handle, and reading `TokenStatistics`,
   which includes `auth_id`. No dedicated enumeration syscall exists
   or is needed.
3. authd requests termination — through peinit for supervised
   services, through signals for user processes.
4. The processes terminate, dropping their token references.
5. The last reference drops and the session object is cleaned up.

Token file descriptors can be passed between processes over IPC, so a
reference held by a process outside the target session survives that
session's process termination. authd has to account for this when
enumerating token holders — the walk finds processes running under the
session, not every process holding one of its tokens.

Kernel-side invalidation — a dead flag on the LogonSession object
checked during AccessCheck, so that access checks against its tokens
fail immediately — is not implemented.
