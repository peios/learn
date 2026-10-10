---
title: Logon types
type: concept
description: Every logon session is tagged with a logon type — Interactive, Network, Batch, Service, NetworkCleartext, NewCredentials, or RemoteInteractive — and what each type means.
related:
  - peios/logon-sessions/overview
  - peios/logon-sessions/lifecycle
  - peios/identity/well-known-principals
---

Every logon session carries a `logon_type` — a single number, set by authd at session creation, that classifies the nature of the sign-in. The type is informational from KACS's point of view: AccessCheck does not branch on it. But it is recorded — by name, such as `interactive` or `network` — in the `kacs.session.destroyed` event that closes the session, and it is what audit consumers and SIEM tools use to distinguish "the user logged in at the console" from "the user logged in over the network" from "a service started under this account".

There are seven types in v0.20.

## The seven types

The numeric values are also catalogued in [Other constants](~peios/advanced-peios/constants-and-catalogs/other-constants).

| Value | Name | What it means |
|---|---|---|
| 2 | **Interactive** | The user signed in at the console, an SSH session, or some other interactive channel. The most common type for human users. |
| 3 | **Network** | The user authenticated to access network resources without an interactive sign-in. Typical for SMB, RPC, federated services. |
| 4 | **Batch** | A scheduled job. The principal is logged in to run a task at a specific time, not by a user actively present. |
| 5 | **Service** | A service started under a specific principal. Used for the long-lived service-account model. |
| 8 | **NetworkCleartext** | A network logon where the credential was transmitted in cleartext over the wire. The session is otherwise a Network session; the type distinction exists for audit. |
| 9 | **NewCredentials** | A session created to use different credentials when reaching out to remote resources, while keeping the local identity unchanged. The local thread continues to act as its primary token; outbound network requests carry the alternative credentials. |
| 10 | **RemoteInteractive** | The user signed in to a graphical desktop on this machine from somewhere else. Interactive in every sense that matters to an access check, but reached over a wire rather than at hardware this machine owns. |

Values 1, 6, 7, and 11 onward are reserved and not used in v0.20.

## When each type is used

### Interactive

The default for any sign-in where a human is at the keyboard. Console logins, SSH connections, terminal services, the lock-screen unlock — all Interactive.

You will see Interactive in audit logs whenever a real user begins a session. If your audit policy distinguishes "human did something" from "automation did something", the Interactive type is the marker for the human side.

### Network

Used when a principal authenticates only to access a network resource — for example, a remote user mounting a file share. The session exists on the server, the user's identity is established there, but the user has no interactive presence on the machine. The session's tokens are typically short-lived (one connection's worth of work).

A Network session is what an inbound SMB connection produces, what an authenticated RPC call produces, what a federated service request produces. It is also what a host typically sees when a user reaches a service on it that is acting on the user's behalf.

### Batch

Scheduled tasks. The principal is "logged in" only in the sense that the system mints a token for the user so the task can run as them. There is no human presence. Once the task finishes, the session ends.

Batch sessions are useful for auditing scheduled work — distinguishing "the user typed this command" from "the user's scheduled task did this command".

### Service

The session under which a service runs. The service account signs in once at service start; the session lives for as long as the service runs. Most services on a Peios machine are Service-type sessions.

This is the type you will see most often in the session listing at `/sys/kernel/security/kacs/sessions` on a system without active interactive users — every running service contributes one Service-type session.

### NetworkCleartext

Used when the authentication protocol exposed the credential in cleartext on the wire. The semantic effect is identical to Network — it is a network sign-in producing a Network-style session — but the type difference exists so audit policy can flag the cleartext exposure.

You should rarely see this in normal operation. Its presence in an audit log is worth attention; it usually indicates that an older or misconfigured protocol is in use.

### NewCredentials

The unusual one. A NewCredentials session does not replace the calling thread's identity. Instead, it represents "I want to keep being myself locally but use these other credentials for outbound network calls". The thread's effective token retains the local user's SIDs and privileges for everything KACS evaluates locally, but any outbound credential-using request carries the alternative principal.

The pattern matters in environments where a user has local rights on one machine and different rights on another, and wants to keep both available without switching sessions.

### RemoteInteractive

A desktop session driven from somewhere else — the user has a screen, a keyboard and a full graphical session, but none of the hardware is here.

GXWI requests this type when logging on through authd. The kernel and authd
must both support value 10; an older authd refuses the request rather than
substituting another type. After updating GXWI and authd, log off existing
GXWI sessions and start new ones: reconnecting to an existing compositor
retains that session's original token and logon type.

It is a separate type from Interactive rather than a flavour of it because the two differ in exactly one respect that an administrator may want to act on: whether the person is physically at the machine. Everything else about the session is the same, which is why a RemoteInteractive token carries the Interactive group SID as well as its own — see [Well-known principals](~peios/identity/well-known-principals) for what that pair lets you write.

Rebooting from a RemoteInteractive session needs `SeRemoteShutdownPrivilege` on top of `SeShutdownPrivilege`, as it does from a Network, NetworkCleartext or NewCredentials session. The screen being remote is what counts, not the session being graphical.

## Where the type appears

The logon type is stamped in three places you will care about:

- **In the session itself**, retrievable through `/sys/kernel/security/kacs/sessions` and the session inspection APIs.
- **In every token's session** — via the token's `auth_id` field, which points to the session, which holds the type.
- **In audit events** — every audit event that includes a subject also implicitly identifies the subject's session, and audit consumers can use that to retrieve the logon type for the event.

The type is **not** part of any token's SID list. There is no "Interactive" SID that gets added to a token's groups based on the logon type. The well-known SIDs like `S-1-5-4` (Interactive) and `S-1-5-2` (Network) are added to a token's groups by authd based on the logon type, but they are independent token attributes from that point on. A token with the Interactive group SID has it because authd put it there; the session's logon_type is the input that drove that decision.

This independence is intentional. A token can in principle carry the Interactive group without belonging to an Interactive-type session (rare, but legal). Audit and ACL evaluation use the group SID; provenance uses the session's type.

## What the type does not affect

AccessCheck does not read the logon type. The DACL walk, the MIC check, the PIP check, the restricted/confinement passes — none of them branch on logon_type.

If you want different access for "Interactive users" vs "Network users", you write ACEs that reference the well-known group SIDs (`S-1-5-4`, `S-1-5-2`, etc.). Those SIDs end up in the token because of the logon type, but the access check matches on the SID, not the type.

The type matters at the seams: when authd is making decisions about which groups to add to a token, when the audit subsystem is recording provenance, when a SIEM correlates events across sessions. Inside the access check itself, the type is invisible.

## Where to go next

For how a session is created, destroyed, and forcibly revoked, read [Session lifecycle](~peios/logon-sessions/lifecycle).

For the well-known group SIDs (`S-1-5-4` Interactive, `S-1-5-2` Network, and the rest) that authd derives from the logon type, read [Well-known principals](~peios/identity/well-known-principals).

To see the logon type of each active session from a shell, read [The logonse command](~peios/logon-sessions/logonse-command).
