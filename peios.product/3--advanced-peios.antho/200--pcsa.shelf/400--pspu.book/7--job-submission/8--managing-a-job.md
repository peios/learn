---
title: Managing a Job
description: The four commands a submitter issues about a job — status, wait, stop, signal — the Security Descriptor every job carries, the rights on it, and who holds them by default.
---

Four commands act on an existing job. Every one is authorised against
the job's own Security Descriptor, using the connection's token, with
the rights and mapping below. There is no command the manager performs
on a job without a check, and no principal exempt from one — the
submitter included.

## Rights

| Right | Bit | Grants |
|---|---|---|
| `JOB_QUERY` | 0x0001 | Read the job view; wait on the job. |
| `JOB_STOP` | 0x0002 | Stop the job. |
| `JOB_SIGNAL` | 0x0004 | Send a signal to the job's process. |
| `JOB_ALL_ACCESS` | 0x0007 | All three. |

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `JOB_QUERY` |
| `GENERIC_WRITE` | `JOB_STOP \| JOB_SIGNAL` |
| `GENERIC_EXECUTE` | `JOB_STOP \| JOB_SIGNAL` |
| `GENERIC_ALL` | `JOB_ALL_ACCESS` |

The same rights and mapping govern the control channel's job commands
(§4.7).

## The job's descriptor

Every job carries a Security Descriptor from the moment its record
exists. Unless the `submit` supplied one, the manager MUST construct:

- owner and group: the submitter's user SID;
- a DACL granting `JOB_ALL_ACCESS` to the submitter, to SYSTEM
  (`S-1-5-18`) and to Administrators (`S-1-5-32-544`);
- nothing else. In particular **the job identity is granted nothing**:
  a process cannot, by virtue of running as U, see or stop a job that
  runs as U. A submitter that wants the principal to see its own
  session says so.

A `submit` MAY supply `security_descriptor`, in SDDL, and the manager
MUST use it as given — it MUST NOT add its default entries to it. The
supplied descriptor MUST carry an owner and a DACL, or the `submit` is
`INVALID_ARGUMENTS`. A submitter that omits itself from the DACL it
supplies has locked itself out of its own job, and the manager MUST
NOT prevent that: the descriptor is the policy, and a policy the
manager second-guessed would not be one.

The descriptor is fixed at submission. This chapter defines no command
to change it.

## status

Returns the job view. Requires `JOB_QUERY`.

## wait

Blocks until a condition holds, then returns the job view. Requires
`JOB_QUERY`.

| `for` | Returns when |
|---|---|
| `terminal` (default) | The job reaches a terminal state. |
| `ready` | The job has sent `READY=1`, **or** reaches a terminal state, whichever first. |

`for: ready` on a `readiness: none` job MUST be answered
`INVALID_STATE`: there is nothing to wait for. On a job that is
already ready, or already terminal, the manager MUST answer at once.

A connection blocked on a `wait` is not idle (§7.3). The wait is
bounded by nothing but the job: a `wait` on a session job with no
`timeout` blocks until something stops it. A submitter that needs a
bounded wait polls `status` instead, or waits on the process handle it
was given.

If the job's record is dropped while a wait is blocked on it — which
can only happen after it became terminal and its grace period elapsed,
so only if the manager was unable to answer in time — the wait MUST
be answered `UNKNOWN_JOB`.

## stop

Asks the manager to end the job. Requires `JOB_STOP`.

The manager MUST send the termination signal to the job's process,
wait `stop_timeout`, and then kill everything remaining in the job's
containment. A job that has sent `STOPPING=1` MUST NOT receive the
termination signal (§4.19); the deadline still applies.

`wait` defaults to **true**: the response is sent when the job is
terminal. With `wait: false` the manager MUST respond as soon as the
stop has been initiated, with the job view as it then is.

A `stop` on a job that is already terminal MUST return the job view
unchanged, with `"status": "ok"`. It is not an error to stop something
that has stopped; it is a no-op, and the view is the honest answer. A
second `stop` on a job already being stopped MUST NOT restart the
deadline.

## signal

Sends one signal to the job's main process, and nothing else. Requires
`JOB_SIGNAL`.

`signal` MUST be an integer naming a signal the platform defines, or
the request is `INVALID_ARGUMENTS`. The manager MUST deliver it to
the process through the handle it obtained at fork, so that a recycled
PID can never be signalled by mistake, and MUST answer with the job
view.

A `signal` on a job that is not `running` MUST be answered
`INVALID_STATE`.

This is the raw mechanism, deliberately: `SIGKILL` through `signal`
kills the main process and leaves whatever it spawned, and produces a
`failed` job with `exit_signal` set and a null `cause`. A submitter
that wants the job *ended* uses `stop`.

## What none of them do

None of these commands moves a job backwards or starts it again. A
terminal job stays terminal, its record is dropped after the grace
period, and a submitter that wants the program to run again submits
it again.
