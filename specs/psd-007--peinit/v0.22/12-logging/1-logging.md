---
title: Service Output Handling
---

peinit is not a logging system. eventd handles log storage,
indexing, and queries. But peinit holds the pipes at birth -- it
controls where service output goes, and it must handle the window
before eventd is running.

## Output wiring

When peinit forks a service process, it MUST create pipes for
stdout and stderr before exec. The child's stdout and stderr are
redirected to the write end of these pipes. peinit holds the read
end and monitors them via epoll.

The parent-held read ends of service stdout/stderr pipes MUST be made
nonblocking before they are monitored by the event loop. This
nonblocking setting applies to peinit's read ends only; the
child-facing stdout/stderr write ends MUST retain ordinary blocking
pipe semantics so pipe backpressure continues to slow an overproducing
service instead of converting normal writes into `EAGAIN` failures.

The event-loop epoll instance is peinit-owned runtime state. It MUST be
created close-on-exec, and service children MUST NOT inherit it.

The child's stdin MUST be redirected to `/dev/null`. peinit does
not provide an interactive input channel to services; a service
that requires input MUST obtain it through an explicit mechanism
(a socket or a stored fd), never inherited stdin.

peinit MUST read service output line-by-line and tag each line
with:

- Service name.
- Stream (stdout or stderr).
- Timestamp (CLOCK_REALTIME).
- Job GUID.

ExecStartPre and ExecStartPost hook output MUST be captured and
tagged with the service name and hook identifier (e.g.,
`jellyfin/ExecStartPre[0]`).

Health check output MUST be captured -- useful for diagnosing why
a health check failed.

## Pre-eventd log buffer

Before eventd starts there is nowhere to send service logs --
eventd's log datagram socket does not exist until eventd binds it.
peinit MUST therefore buffer captured stdout/stderr in a fixed-size
in-memory pre-eventd log buffer (default 1 MB). When the buffer
fills, the oldest entries MUST be dropped.

peinit's own audit records (access denials, critical failures,
recovery-mode entry, graph errors, security-relevant state
transitions) are **events, not logs**: peinit emits them via KMES
(`kmes_emit`), and the KMES kernel ring buffer persists them from
the moment PKM loads -- before eventd, before the registry. peinit
therefore keeps NO pre-eventd buffer for them; eventd picks them up
from the kernel ring buffer when it attaches (see §11.1).

> [!INFORMATIVE]
> In practice, the only services that run before eventd are
> registryd, lpsd, authd, and eudev. The first three are Peios-
> owned with controlled output. eudev is the primary overrun risk
> (verbose device enumeration). The restart budget naturally bounds
> output from crash loops.

## Flood protection

A noisy service MUST NOT starve peinit's event loop. The following
limits apply:

| Registry key | Default | Description |
|---|---|---|
| `Machine\System\Init\MaxLogLineLength` | 8192 | Maximum bytes per line. Lines exceeding this are truncated with a `[truncated]` marker. |
| `Machine\System\Init\MaxLogBufferPerService` | 65536 | Maximum bytes buffered per service pipe before backpressure. |

### Per-iteration read budget

In each event loop iteration, peinit MUST read at most a bounded
number of bytes from service pipes before returning to process
other events (signals, control socket, notify socket, timerfds).
The exact budget is an implementation tuning parameter.

### Backpressure

If a service writes faster than peinit can read from its pipe, the
kernel pipe buffer fills and the service's `write()` calls to
stdout/stderr block. This is deliberate -- the service naturally
slows down. Backpressure via the pipe is the flow-control mechanism
between the service and peinit; at this stage peinit MUST NOT drop
output -- it MUST keep reading the pipe within its per-iteration
budget.

Downstream of the pipe, delivery is loss-tolerant by design: the
pre-eventd log buffer drops oldest entries when full, and eventd's
datagram log socket may drop records under load (see Lossy log
delivery). The no-silent-drop guarantee covers reading the pipe,
not delivery to eventd -- logs are a best-effort path. Audit
*events* are not subject to this loss; they go through KMES.

## Event loop fairness

No single event source MAY starve the event loop. peinit's event
loop MUST cycle back to signal processing (SIGCHLD reaping,
shutdown signals) within bounded time regardless of load on any
other source.

Signals MUST never be starved. Child reaping and shutdown handling
take priority over all other event sources in every iteration.

## eventd handoff

When eventd reaches Active state:

1. peinit MUST begin sending to eventd's log datagram socket (path
   from `Machine\System\eventd\LogSocketPath`).
2. peinit MUST replay the pre-eventd log buffer (oldest first),
   preserving each line's timestamp and metadata. This replay is
   **best-effort**: the records are msgpack datagrams on a
   loss-tolerant socket (PSD-008 §4.2), so some MAY be dropped by
   the kernel under load. peinit MUST NOT block waiting to deliver
   them.
3. peinit MUST switch to real-time forwarding -- new service output
   is sent as it arrives, as msgpack records (batched as an array
   of maps under load).
4. The pre-eventd log buffer is cleared.

From this point, peinit is a pipe relay: read from service pipes,
tag each line with metadata (service name in `origin`, stream in
`is_error`, the line timestamp, and the job's `job_id`), and
forward as msgpack datagrams. Audit records continue to flow as
KMES events, independent of this log path.

### Lossy log delivery

The eventd log socket is a non-blocking Unix datagram socket. If
eventd cannot drain it fast enough, its `SO_RCVBUF` fills and the
kernel drops further datagrams silently (PSD-008 §4.2) -- log
ingestion MUST NOT exert backpressure on senders. peinit therefore
keeps no stream-style outbound write buffer: it sends each record
(or batch) as a datagram and accepts that some MAY be dropped under
load.

peinit MUST NOT block on a send to eventd and MUST NOT allow
unbounded memory growth from pending log records.

## eventd failure

If eventd crashes after it was running:

1. peinit detects eventd's exit (it supervises eventd as a service)
   and re-enables the pre-eventd log buffer.
2. When eventd restarts and reaches Active, the handoff sequence
   repeats (best-effort replay).

There is a log gap between eventd crashing and restarting, bounded
by the pre-eventd log buffer size. Events are unaffected: they
continue to land in the KMES kernel ring buffer regardless of
eventd's state, and eventd resumes consuming them from the last
persisted sequence when it restarts.

## Console output

peinit MUST write its own operational messages to `/dev/console`:

- Phase 1 progress (mount results, registryd start).
- Phase 2 progress (service start/fail, dependency errors).
- Shutdown progress.
- Recovery mode entry.
- Critical service failures.

Service stdout/stderr MUST NOT be echoed to the console by default.
The console is for peinit status messages only.
