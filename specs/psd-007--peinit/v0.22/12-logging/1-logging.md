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

## Pre-eventd buffer

Before eventd starts, peinit MUST buffer all captured output in
fixed-size in-memory pre-eventd ring buffers:

| Buffer | Default size | Contents |
|---|---|---|
| Service output | 1 MB | stdout/stderr from pre-eventd services. |
| Audit | 256 KB | peinit's own events -- access denials, critical failures, recovery mode entry, graph errors, security-relevant state transitions. |

The audit buffer is separate and additive. A noisy service MUST NOT
crowd out audit events.

When either buffer fills, the oldest entries MUST be dropped.

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

If a service writes faster than peinit can forward to eventd (or
than the pre-eventd ring buffer can absorb), the service's pipe
buffer fills. When the kernel pipe buffer is full, the service's
`write()` calls to stdout/stderr block. This is deliberate -- the
service naturally slows down.

peinit MUST NOT drop service output silently. Backpressure via the
pipe is the flow control mechanism.

## Event loop fairness

No single event source MAY starve the event loop. peinit's event
loop MUST cycle back to signal processing (SIGCHLD reaping,
shutdown signals) within bounded time regardless of load on any
other source.

Signals MUST never be starved. Child reaping and shutdown handling
take priority over all other event sources in every iteration.

## eventd handoff

When eventd reaches Active state:

1. peinit MUST connect to eventd via its IPC socket.
2. peinit MUST drain the entire service output pre-eventd ring
   buffer to eventd (oldest first), preserving timestamps and
   metadata.
3. peinit MUST drain the audit pre-eventd ring buffer to eventd.
4. peinit MUST switch to real-time forwarding -- new service output
   is sent to eventd as it arrives.
5. The pre-eventd ring buffers are cleared.

From this point, peinit is a pipe relay: read from service pipes,
tag with metadata, forward to eventd.

### Outbound write backpressure

The eventd socket is non-blocking. If eventd processes data slower
than services generate it, the kernel socket buffer fills. peinit
MUST maintain a bounded outbound write buffer (same 1 MB limit as
the pre-eventd ring buffer). When the outbound buffer fills, oldest
messages are dropped.

peinit MUST NOT block on a write to eventd and MUST NOT allow
unbounded memory growth from pending writes.

## eventd failure

If eventd crashes after it was running:

1. peinit detects the disconnection (socket closes).
2. peinit re-enables the pre-eventd ring buffers.
3. When eventd restarts and reaches Active, the handoff sequence
   repeats.

There is a log gap between eventd crashing and restarting, bounded
by the pre-eventd ring buffer size.

## Console output

peinit MUST write its own operational messages to `/dev/console`:

- Phase 1 progress (mount results, registryd start).
- Phase 2 progress (service start/fail, dependency errors).
- Shutdown progress.
- Recovery mode entry.
- Critical service failures.

Service stdout/stderr MUST NOT be echoed to the console by default.
The console is for peinit status messages only.
