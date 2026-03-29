---
title: Sessions and Revocation
order: 7
---

## Logon sessions

A logon session is a lightweight kernel object identified by a LUID (`auth_id`). Every token references a logon session.

- **Creation** — authd creates a logon session (via KACS syscall) at authentication time, before creating the token. The session records the authentication type (Interactive, Network, Service, etc.) and creation timestamp.
- **Association** — each token's `auth_id` references its logon session. Multiple tokens MAY share a session (linked pairs, tokens derived via duplication).
- **Cleanup** — when the last token referencing a logon session is freed (refcount drops to zero), the kernel destroys the session object and notifies authd asynchronously. authd uses this notification to clean up associated credentials (cached Kerberos tickets, etc.).

Logon sessions are bookkeeping. No access control decision depends on the logon session — AccessCheck MUST NOT consult `auth_id`. The `interactive_session_id` field is similarly metadata; the kernel stores it and returns it on query but no kernel security mechanism evaluates it.

## Token expiration

The token's `expiration` field carries a timestamp. In v0.20, this field MUST NOT be enforced by AccessCheck — it is informational only.

Token lifetime is governed by reference counting, not by the expiration timestamp. Tokens exist as long as at least one reference (process credential or open file descriptor) exists.

## Revocation

KACS does not provide a token revocation primitive. There is no "invalidate token X" or "kill session Y" syscall.

Session termination is userspace coordination:

1. authd decides a session must end (admin request, security incident, account deletion, or user-initiated logoff).
2. authd enumerates processes whose tokens carry the target `auth_id` or `interactive_session_id`.
3. authd requests process termination — via peinit for supervised services, via signals for user processes.
4. Processes terminate, dropping their token references.
5. When the last reference drops, the logon session object is cleaned up.

> [!INFORMATIVE]
> Token file descriptors can be passed between processes via IPC. A token reference held by a process outside the target session will survive the session's process termination. authd must account for this when enumerating token holders.

> [!INFORMATIVE]
> Kernel-side session invalidation (marking a logon session as dead so that new access checks against its tokens fail immediately) is a future enhancement. The mechanism would be a dead flag on the logon session object, checked during AccessCheck. This is not part of v0.20.
