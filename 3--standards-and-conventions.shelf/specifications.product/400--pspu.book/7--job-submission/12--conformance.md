---
title: Conformance
description: Every requirement of this chapter collected by role — manager and submitter — and what a job owes, which is nothing this chapter did not already ask of a service.
---

## A conforming manager

**The socket.** Listens on a Unix sequenced-packet socket at the
well-known path, close-on-exec on the listener and every accepted
connection, and ensures the socket and each directory containing it
carry a Security Descriptor admitting exactly the principals meant to
submit. Performs no access check of its own before a `submit` (§7.3).

**Messages.** Emits and accepts exactly one compact JSON object per
record, with no terminator. Receives every message with room for one
token and the maximum number of descriptors, answers a truncated
message or attachment list without acting on it, and closes every
attached descriptor it does not hand on or adopt, on every path (§7.4).

**Identity.** Establishes the submitter from the kernel once, at
accept. Installs on a job exactly one of: the connecting process's own
primary token, opened through the kernel's peer process handle; or
the token the kernel attached to the `submit`, duplicated to a
primary. Refuses a token below Impersonation level, more than one
token, or one it cannot duplicate, with `BAD_TOKEN`. Accepts no
identity by name and no primary token by plain descriptor (§7.5).

**Submission.** Validates the definition as §7.6 lists and refuses with
`INVALID_ARGUMENTS`; does not check that the program exists. Checks
identity and quota before creating any record. Answers a `submit` when
the job has left `created` and not before or after, with the job view,
attaching the process handle when the job is running (§7.6).

**The job view.** Reports every job in the one shape of §7.7, with
every inapplicable field present and null, the state-dependent
population rules honoured, and the cause set only where the manager
decided the outcome. Holds a terminal record for the grace period and
answers a dropped or never-existent identifier `UNKNOWN_JOB` alike.

**Management.** Gives every job a descriptor — the default of §7.8 or
the one supplied — and checks every command against it with the
rights and mapping there, including commands from the submitter.
Implements `status`, `wait`, `stop` and `signal` with the semantics of
§7.8: a `wait` bounded only by the job, a `stop` that is a no-op on a
terminal job and does not restart a running deadline, a `signal`
delivered through the fork-time handle.

**Descriptors and output.** Injects attached descriptors from 3 upward
with `LISTEN_FDS`, `LISTEN_FDNAMES` and `LISTEN_PID` set; records the
job's output unconditionally; and, when asked, copies it to a
non-blocking sink, dropping for the sink only, counting and reporting
the drops, and closing the sink when the job ends (§7.9).

**Errors and extension.** Emits only the codes in §7.10, ignores
unrecognised request fields, and adds nothing from §7.11's closed
list — and never an identity or policy field — without a negotiated
version.

## A conforming submitter

Connects as the identity it wants to own its jobs, and conveys any
other identity per message rather than by impersonating at connect.
Attaches at most one token, and sets its connection's level to
Delegation before attaching when the job needs it. Sends one compact
JSON object per record. Supplies every `LISTEN_FDNAMES` name it
attaches a descriptor for, and none containing `:`. Assumes the
manager owns every descriptor it attached. Treats an immediate close
with no response as a refusal. Does not parse `message`. Accepts null
for every nullable field and unrecognised fields in the job view.
Treats an unrecognised state, cause, unit or error code as an error
for that request rather than guessing. Reads `state` rather than
`cause` to decide whether a job succeeded. Uses `stop` to end a job
and `signal` only to signal it. Does not depend on a job's record
surviving its grace period.

## A conforming job

Nothing beyond §4.22's requirements of a service on the notification
channel. A job that sends progress does so in the form §4.19 defines.
A job that adopts descriptors checks `LISTEN_PID` first.

## What conformance is not

A manager that offers the control channel and not this one is still a
conforming manager under §4. This chapter is the contract for one that
offers both.
