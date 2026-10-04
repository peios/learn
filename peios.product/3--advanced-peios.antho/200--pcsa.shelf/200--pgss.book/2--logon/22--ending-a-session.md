---
title: Ending a Session
description: How a caller asks the authority to end a logon session — the question and the act as separate messages, who may end whose, what the authority ends and what it cannot reach, and the answer that goes first when the caller is in the session.
---

A caller asks the authority to end a logon session with `SessionEnd`,
and asks whether it may with `SessionEndQuery`. Each is a whole
conversation in one message, on `/run/logon.sock`: the client sends it
first and alone, and the authority answers with one terminal message.

```
client                                   authority
  |                                          |
  |------------ SessionEndQuery ------------>|   may I?
  |<-- SessionEndAllowed | AccessDenied -----|   nothing changed
  |                                          |

client                                   authority
  |                                          |
  |-------------- SessionEnd --------------->|   end it
  |                                          |   (ends its processes)
  |<---- SessionEnded | AccessDenied --------|   terminal
```

§2.3's rules hold for both: one per connection, the request as the
first and only client message, exactly one terminal message, and the
connection closed after it.

## Why the authority

The kernel has no call that ends a logon session. A session lasts as
long as a token of it does, and is destroyed when the last reference
goes (Kernel TRM §3.2.7). Ending a session is therefore ending the
processes that run in it, after which the kernel does the rest.

Any sufficiently privileged program could do that walk. It belongs to
the authority for two reasons.

**One decision, one record.** The authority created the session and is
the component the standard already trusts to decide who may do what
with logons. A desktop's task manager, a principal manager and a
command-line tool asking it get the same answer, under one policy, and
leave one record of what was ended at whose request.

**It can finish.** A process in the session may be protected, or carry
a descriptor that does not let an administrator end it. A program doing
the walk itself can stop halfway and leave half a session. The
authority, as the most trusted process outside the kernel, can end what
an administrator's tools cannot.

## SessionEndQuery

`msg_type` = `0x0041`. Client to authority. The whole request.

| Field | Encoding | Limit |
|---|---|---|
| `logon_session_id` | `u64` | — |

`logon_session_id` is the session's identifier: the `auth_id` every
token of the session carries.

The authority answers with `SessionEndAllowed` where a `SessionEnd` for
the same session from the same peer would be permitted now, and
otherwise with `AccessDenied` carrying the denial that `SessionEnd`
would draw. It MUST NOT signal any process, or change anything else,
in answering.

It exists so that a program can decide whether to offer the act at all.
A window that shows a person a button that can only fail has told them
something false.

## SessionEnd

`msg_type` = `0x0040`. Client to authority. The whole request.

| Field | Encoding | Limit |
|---|---|---|
| `logon_session_id` | `u64` | — |

The authority ends the session's processes as §2.22 describes below and
answers with `SessionEnded`, or refuses with `AccessDenied`.

## Why the question is a separate message

The two requests have the same body and differ only in `msg_type`. They
could have been one message with a flag saying "only ask". They are not,
for the reason `ServiceAttest` is not a `LogonStart` (§2.19): a flag
puts the path that ends a session on the same dispatch as the path that
must not, separated by one bit. With two messages, a probe cannot end a
session by any corruption or confusion of a field — only by being a
different message.

An authority MUST NOT accept either message as the other.

## Who may end a session

The caller is the **user of the connected peer's token**, established
from the socket as §2.4 requires. An authority MUST refuse, with
`PermissionDenied`, a peer whose token is restricted: a restricted token
does not speak for its user's whole authority.

Unlike `CredentialChangeStart` (§2.20), these messages name their
subject. They have to: the usual caller is an administrator, and the
session is somebody else's. What the name buys is decided entirely by
who is asking.

An authority MUST apply the following, in this order.

1. **Never the kernel's sessions, never a service's.** An authority
   MUST refuse, with `PermissionDenied`, the session the kernel creates
   for SYSTEM, the one it creates for Anonymous, and every session whose
   logon type is `Service` — whoever asks, the session's own user and
   SYSTEM included. Every process on the machine descends from the first
   and depends on it. A service is stopped through the service manager,
   which knows how to stop it and whether to start it again; signing it
   out from under that manager does neither.
2. **Your own session.** An authority MUST permit a caller to end a
   session whose user is the caller, whose logon type is one a person
   has — one of those §2.B lists, other than `Service` — and whose user
   is a principal of an issued domain (`S-1-5-21-A-B-C-RID`). No grant
   is needed: signing yourself out is not a privilege. A well-known
   identity is not a person signing out, whatever its session's type.
3. **Anybody else's.** Otherwise, an authority MUST decide by an access
   check of the caller's token, for a right that means "end a session",
   against a security descriptor its local policy states.
   - Where local policy states no descriptor, the authority MUST permit
     SYSTEM and Administrators and nobody else.
   - Where it states one that cannot be used — the wrong type, empty,
     unreadable, or not a descriptor — the authority MUST permit nobody,
     and SHOULD record why. Falling back to the default would grant more
     than the site wrote to anybody the site meant to exclude, and
     nobody would notice; refusing everybody is noticed at once.
4. **No such session.** Where the session does not exist, an authority
   MUST answer `NoSuchSession` to a caller rule 3 permits, and
   `PermissionDenied` to any other.

The last rule is about disclosure. Which sessions exist — who is signed
in, and since when — is not something every principal may list, and a
`NoSuchSession` that differed from a refusal would let anybody who can
reach the socket enumerate sessions by number.

`PermissionDenied` and `NoSuchSession` are the only denials these
messages draw for a decision. `MalformedRequest`, `UnsupportedVersion`
and `Internal` keep their usual meanings (§2.10).

> [!NOTE]
> On Peios the descriptor is the `REG_SZ` value `SessionEndSecurity` on
> `Machine\Generic\Authn\Policy`, in SDDL, read on every request. The
> right is `0x1`, and every generic right maps to it. With the value
> absent the descriptor is `O:SYG:SYD:(A;;0x1;;;SY)(A;;0x1;;;BA)`. The
> kernel's sessions are 999 (SYSTEM) and 998 (Anonymous).

## What the authority ends

An authority MUST end every process whose **primary** token belongs to
the session, by asking each to terminate, giving it a grace period, and
then terminating whatever is left without asking.

It MUST NOT signal a process because one of its threads is impersonating
a token of the session. A service that impersonates a person to answer
one request is not in that person's session, and ending it would end the
service for everybody.

It MUST address each signal to the process whose token it examined, by
a reference that cannot come to name a different process — never by a
process identifier looked up again, which may have been reused in the
meantime.

A process can start another during the grace period, and the new one
holds the session too. So after each round an authority MUST look again,
and end what it finds in a further round. It MUST bound the number of
rounds, and MUST bound the grace period. Both bounds are
implementation-defined, but the grace period MUST NOT exceed 10 seconds,
and the whole request MUST be answered within 60 seconds, which is what
a client may wait.

A process the authority cannot examine, or cannot signal, is not a
failure of the request. It is counted in `remaining`, and the authority
carries on with the rest.

An authority MUST NOT end its own process, and MUST NOT hold a token of
the session for longer than it takes to read which session the token
belongs to. Each token held is a reference that keeps the session alive.

An authority SHOULD record each `SessionEnd` it acts on — who asked,
which session and whose it was, and the counts it answered — wherever
it records logons.

This is the one thing the authority does to processes. It starts none,
and §2.1's prohibition stands.

> [!NOTE]
> Mainline's authority finds the session in
> `/sys/kernel/security/kacs/sessions`, walks `/proc`, opens each
> process by `pidfd_open` and reads its primary token through
> `kacs_open_process_token` on that pidfd, so the signal it later sends
> by `pidfd_send_signal` reaches the process whose token was read. It
> sends `SIGTERM`, waits up to 5 seconds for everything signalled to
> exit, sends `SIGKILL` to what is left, waits up to 1 second, and walks
> again — at most three rounds, so at most about 18 seconds.

## SessionEnded

`msg_type` = `0x8040`. Authority to client. The successful terminal
message of `SessionEnd`; nothing follows it.

| Field | Encoding | Limit |
|---|---|---|
| `ended` | `u32` | — |
| `remaining` | `u32` | — |

`ended` is the number of processes of the session the authority
signalled that its last look no longer found.

`remaining` is the number of processes its last look did find still
holding the session, plus those it could not examine. Not zero means the
session may still exist, and a client SHOULD say so rather than report
the person signed out.

Both fields are mandatory. The message is newer than the rule that lets
a trailing field be absent, so there is no older authority whose silence
needs a default.

The counts are of processes, not of references. A session outlives its
processes wherever a reference the authority cannot see survives them —
see below — and such a reference is counted nowhere.

## SessionEndAllowed

`msg_type` = `0x8041`. Authority to client. The successful terminal
message of `SessionEndQuery`; nothing follows it. It has no fields.

## When the caller is in the session

A caller may end the session it is running in, and a person signing
themselves out usually does. Ending it ends the caller, and the
authority cannot answer a connection whose other end is gone.

So where the session being ended is the one the connected peer's token
belongs to, an authority MUST send `SessionEnded` **before** it signals
anything. Its `ended` is then the number of processes it found to end,
and `remaining` is zero: the counts say what the authority is about to
do, not what it achieved. It then ends the session exactly as it would
any other.

A client in that position MUST NOT read the counts as an outcome, and
SHOULD expect to be ended shortly after it reads them.

The connection is itself a reference to the caller's token, held by the
authority's end of the socket, so the session is not destroyed until the
authority has closed it.

## What ending a session cannot reach

The kernel destroys a session when its last reference goes, and some
references are not processes running in the session:

- **A token descriptor held elsewhere.** A token can be passed between
  processes as a descriptor (Kernel TRM §3.2.7). A process outside the
  session holding one keeps the session alive after every process in it
  has ended, and nothing here finds it.
- **An impersonating thread.** By the rule above, a thread of another
  process impersonating a token of the session is not ended. The session
  lasts until that thread reverts.
- **A process not yet reaped.** A process that has exited still holds
  its token until its parent reaps it. It counts in `remaining`, and
  ending its parent, where that is in the session, usually releases it.

An authority is not required to find these, and a client MUST NOT
assume that `remaining` of zero means the session is gone.

## Access to the socket

Every principal permitted to end its own session needs connect access to
`/run/logon.sock`. That is the same population §2.20 admits, and as
there, reaching the socket permits nothing by itself.

## An authority that does not offer it

An authority MAY decline to offer ending sessions. One that declines
MUST refuse both `SessionEnd` and `SessionEndQuery` with
`PermissionDenied`, and is conforming.
