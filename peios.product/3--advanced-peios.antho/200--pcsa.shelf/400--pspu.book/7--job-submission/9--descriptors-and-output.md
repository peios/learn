---
title: Descriptors and Output
description: Handing descriptors to a job at submission, in the form a conforming program already adopts; and receiving a copy of the job's output while the manager keeps the record.
---

## Descriptors into the job

A `submit` MAY attach descriptors with `SCM_RIGHTS`. The manager MUST
give them to the job's process, in the order they were attached, in
exactly the form §4.20 gives stored descriptors back to a service:

1. Placed consecutively from descriptor **3**, with close-on-exec
   cleared.
2. `LISTEN_FDS` set to the count.
3. `LISTEN_FDNAMES` set to the names from `descriptors`,
   colon-separated, in the same order.
4. `LISTEN_PID` set to the job process's own PID.

All four MUST be absent when nothing is passed.

`descriptors` names them. It MUST have exactly one entry per
descriptor to be injected — the attached descriptors, less the output
sink if `output` is true — or the `submit` is `INVALID_ARGUMENTS`. A
name MUST be non-empty and MUST NOT contain `:`, since `:` is the
separator in `LISTEN_FDNAMES`.

A submitter MAY attach nothing and send an empty `descriptors`; that
is the common case.

> [!NOTE]
> This is what makes a session job possible without inventing a
> channel: the submitter creates a `socketpair`, keeps one end, and
> attaches the other, and the session process finds it at descriptor 3
> under whatever name the submitter chose. It is also what makes a
> terminal possible — attach the pseudo-terminal's slave — and every
> other case where the program needs a handle its submitter already
> holds. The convention is `sd_listen_fds`'s, so a program written to
> adopt descriptors from a service manager adopts them from a
> submitter unchanged.

The manager MUST NOT inspect, validate or restrict what an attached
descriptor refers to. What a job may do with a descriptor is decided
by the rights cached on it, which the submitter established when it
opened it.

## The job's output

A job's standard output and standard error MUST be captured by the
manager and recorded exactly as a service's are — the manager's own
design says where, and on Peios that is eventd, tagged with the job's
identifier. This is unconditional: a submitter cannot turn it off, and
cannot redirect the job's streams somewhere the manager does not see.

A submitter MAY additionally ask for a copy. With `output: true`, the
**last** attached descriptor is not injected into the job; the manager
adopts it as an **output sink** and writes to it every line it reads
from the job's streams, as it reads them.

The copy is best-effort, and the record is not:

- The manager MUST NOT block on the sink, and MUST NOT let a sink that
  is not being drained slow the job or the manager. It MUST put the
  sink in non-blocking mode.
- When a write to the sink would block, the manager MUST drop the line
  **for the sink only**, MUST still record it, and MUST count the drop.
  It MUST report that drops occurred — at least once per job, through
  its event stream — so a submitter that sees a gap can learn it
  caused one.
- The manager MUST close the sink when the job is terminal, after the
  last line has been written or dropped, and MUST close it at once if
  writing to it fails with anything other than a would-block
  condition.

What the manager writes to the sink is each line the job produced,
followed by a newline, with no tagging: the submitter attached the
sink knowing which job it was for. Lines from the two streams are
interleaved in the order the manager read them. A submitter that needs
to tell them apart, or needs every line, reads the record instead.

`output: true` with no attached descriptor is `INVALID_ARGUMENTS`.
