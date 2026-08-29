---
title: The Notification Socket
description: The datagram socket services report on themselves over — authenticating a sender, applying a datagram, and the bounds on it.
---

peinit binds one Unix datagram socket for service notifications, by
default at `/run/services/peinit/notify.sock`. Its path is an
implementation detail: services receive it through `NOTIFY_SOCKET` and
nothing hardcodes it. The kernel command line can override it with
`peios.notifysocket=`.

There is one socket, not one per service, and the bind unlinks any stale
path first. It carries the same inherited descriptor as the control
socket (§10.1).

The protocol itself is PSPU §4. What follows is how peinit decides
whether to believe a datagram.

## Authenticating a sender

`SO_PASSCRED` is enabled on the socket, so every datagram arrives with a
kernel-attested `SCM_CREDENTIALS` control message. A datagram without one
is rejected outright. Descriptors for the fd store arrive alongside, as
`SCM_RIGHTS`.

Authentication then runs five steps, and each closes a hole the previous
one leaves:

1. **Find the sender.** Scan for the current *service-main* job whose
   PID equals the sender's. Only a main job is ever a candidate, which
   is what makes `NotifyAccess=Main` the only mode there is — a hook or
   a health check cannot notify on a service's behalf. If no service's
   main job carries the PID, the live submitted jobs (§8.5) are
   scanned instead. The routing question is asked purely by PID, before
   either door verifies anything, so that a sender is verified against
   its pidfd exactly once whichever way it is routed.
2. **The job is Running.** A job still in pending setup has not exec'd.
3. **The job has a pidfd.**
4. **The pidfd still refers to that PID.** This is the step that
   matters: PID matching alone is racy, because a PID can be recycled
   between the sender writing and peinit reading. The pidfd was obtained
   atomically at fork, so verifying the PID against it is what makes the
   match sound rather than probable.
5. **The generation matches.** A job whose activation generation is
   not the service's current one is a previous incarnation, and its
   notifications are rejected. This is invariant 5 of §6.1 in force: a
   `READY=1` from the process that just crashed cannot mark its
   replacement ready. A submitted job has no generation and no
   replacement, so for it the check stops at step 4.

Anything that fails is dropped and recorded as a `notify.rejected` event
carrying the sender's PID and the reason.

The UID and GID in the credentials are parsed and never used. They are
not policy inputs, and peinit does not consult them for anything —
identity on Peios is a token, and the token here is established by
which job the sender *is*, not by what UID it claims.

## Applying a datagram

A datagram may carry several newline-separated lines, and peinit applies
every one. Parsing happens before application and is all-or-nothing: if
any line is malformed, nothing from that datagram is applied, and any
descriptors it carried are dropped and closed. Partial application of an
ambiguous service-control message is structurally impossible rather than
merely avoided.

A rejection is recorded after authentication, so the event can name the
service where one could be established.

## What the fields do

Most are handled elsewhere: `READY=1` and `RELOADING=1` in §6.5,
`WATCHDOG=1` and `WATCHDOG_USEC` and `EXTEND_TIMEOUT_USEC` in §6.6,
`STOPPING=1` in §12.2, and the fd store fields in §10.6. What each does
to a submitted job — and which are ignored for one, since a job has no
reload, watchdog or store — is in §8.5, along with `PROGRESS=` and
`PROGRESS_UNIT=`, which only a submitted job retains.

Three are event-emitting. `STATUS=`, `ERRNO=` and `EXIT_STATUS=` are
authenticated and then emitted as KMES events — `notify.status`,
`notify.errno`, `notify.exit_status` — whose payloads carry the service
name, the job identifier, the operation identifier and the activation
generation, alongside the value. They take the same path as job and
operation events, not a forward to eventd.

`STATUS=` is additionally stored on the service's runtime state and
exposed as `status_text` in a status query. It is cleared to null at the
start of every activation generation, in the same step that increments
the generation, so a status string cannot survive a restart and describe
a process that no longer exists.

`ERRNO=` and `EXIT_STATUS=` are not stored. They are emitted and
otherwise not retained.

## Bounds

A datagram is read into a fixed 64 KiB buffer, and the control message
buffer is sized for 64 descriptors. Neither `MSG_TRUNC` nor `MSG_CTRUNC`
is inspected, so a larger datagram is truncated silently and descriptors
beyond the sixty-fourth are dropped by the kernel before peinit sees
them.
