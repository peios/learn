---
title: Resource Exhaustion
description: Descriptors, processes, memory and disk running out — how each reaches single-threaded PID 1, and what the OOM killer does.
---

peinit is single-threaded PID 1, so most resource pressure reaches it as
a failure at a syscall rather than as slowness.

## Descriptors

peinit holds a descriptor per supervised process (a pidfd), two per
supervised process for output pipes, one per armed timer, one per
control connection, two per jobs connection (the socket and the peer's
pidfd), one per submitted job's output sink, plus the sockets, the
epoll instance and the signalfd. A submission also holds its prepared
token and attached descriptors from acceptance until the launch takes
them, which is bounded by `MaxJobsPerSubmitter` times the descriptor
cap per message.

`EMFILE` or `ENFILE` from `pipe2` or `clone3` fails the start with
`ParentSetupFailure` — a restart-eligible cause, so a service that
failed because the system was momentarily out of descriptors gets
another go.

Two paths leak descriptors slowly: the pre-start check helper's result
descriptor and pidfd are unregistered from the event loop but not
closed, so a service using filesystem conditions leaks two per start.

## Processes

`EAGAIN` from `clone3` — the PID limit — is also `ParentSetupFailure`
and restart-eligible.

The one path that forks outside the launch machinery is the timer
last-run write, one child per firing of a persistent timer (§9.2). The
children `_exit` as soon as the write returns and peinit matches each
one's exit status back to its write, so a failure is reported rather
than discarded — but the fork itself is real and happens on every firing.

It is a fork of PID 1, so the child briefly inherits everything peinit
holds: every pidfd, the epoll instance, both sockets, every service's
pipe read end. It uses none of them and exits immediately. Driving the
write through an asynchronous LCS path instead would remove the fork
entirely; there is no such path today.

## Memory

`ENOMEM` from `clone3` behaves like the others.

peinit's own memory is bounded by design in the places that could
otherwise grow without limit: the pre-eventd buffer has a fixed size and
drops its oldest, there is no outbound queue for log delivery, terminal
jobs and operations are dropped rather than retained, and neither has a
history structure.

Two things do accumulate. Graph execution contexts and their operation
associations are never retired, so each boot and each on-demand start
adds one for the life of the process. And an `OnFailure` chain entry for
a handler that starts and stays running is never cleared, so it
permanently occupies a slot of that failure's depth budget.

## Disk

A full root filesystem shows up in three places. The boot attempt
counter cannot be written, which peinit treats as a counter of zero and
continues — a failure to record an attempt is not itself worth
escalating. The random seed cannot be saved at shutdown, which is
recorded and does not block the shutdown. And registryd cannot write,
which is registryd's problem and reaches peinit as a Critical service
failing.

## The OOM killer

An `ErrorControl=Critical` service is marked OOM-immune, with
`oom_score_adj` at `-1000`; everything else is left at the default
(§5.4). A Critical service is one whose loss reboots the machine, so
letting the OOM killer pick it would turn memory pressure into a reboot.

peinit itself is PID 1 and the kernel will not choose it.
