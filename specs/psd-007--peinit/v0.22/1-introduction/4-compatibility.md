---
title: Compatibility
---

peinit is the init system of Peios. It is not a port or
reimplementation of systemd, Windows SCM, or any other service
manager. The design choices -- KACS-integrated identity, registry-
based configuration, operations as first-class objects, jobs as
observable execution units -- were made because they solve the
problems Peios needs solved.

Several interfaces are compatible with existing conventions where
compatibility serves Peios's goals. This compatibility is
intentional and maintained.

## sd_notify protocol

peinit supports the sd_notify datagram protocol for service-to-
init communication. Services send `KEY=VALUE` messages to a Unix
datagram socket whose path is provided via the `NOTIFY_SOCKET`
environment variable. A single datagram MAY carry multiple
newline-separated `KEY=VALUE` lines (as in systemd); peinit MUST
parse and apply every line in the datagram. peinit authenticates
senders via kernel-attested PID matching.

The following sd_notify fields are supported:

| Field | Behaviour |
|---|---|
| `READY=1` | Service has completed startup and is ready to serve. Gates dependent startup for services using Notify readiness. |
| `RELOADING=1` | Service is reloading configuration. Extends the reload detection window so peinit waits for `READY=1` completion (§5.3). |
| `STOPPING=1` | Service is shutting down gracefully. Acknowledged by peinit. |
| `STATUS=...` | Human-readable status string. Emitted as a KMES event and exposed via status queries. |
| `ERRNO=...` | Errno-style error number. Emitted as a KMES event. |
| `EXIT_STATUS=...` | Exit status for informational purposes. Emitted as a KMES event. |
| `WATCHDOG=1` | Keepalive ping. Resets the watchdog timer. |
| `WATCHDOG_USEC=...` | Updates the watchdog timeout at runtime. |
| `EXTEND_TIMEOUT_USEC=...` | Requests additional time during start, stop, or reload transitions. |
| `FDSTORE=1` | Pushes the accompanying file descriptor into peinit's per-service fd store for persistence across restarts. |
| `FDNAME=...` | Names a stored file descriptor. Used with FDSTORE for retrieval after restart. |
| `FDSTOREREMOVE=1` | Removes a previously stored file descriptor by name. |
| `FDPOLL=0` | Marks a stored fd as not requiring poll monitoring. |

The following fields are not supported:

| Field | Reason |
|---|---|
| `MAINPID=...` | peinit does not support forking daemons. peinit tracks the process it spawned via pidfd. There is no mechanism for a service to redirect supervision to a different PID. |
| `BUSERROR=...` | D-Bus error reporting. Peios does not use D-Bus. |

Unrecognised fields are silently ignored. This ensures forward
compatibility -- a service compiled against a newer sd_notify
specification will not break when running under peinit.

A malformed sd_notify line is not an unrecognised field. Empty
lines are ignored. A non-empty line is malformed if it lacks `=`,
has an empty key, or otherwise cannot be split into `KEY=VALUE`
form. If any line in a datagram is
malformed, peinit MUST reject the entire datagram, apply no fields
from it, and log the rejection after sender authentication if a
service attribution is available. This prevents partial application
of ambiguous service-control messages.

The exact semantics of each field are defined in their respective
sections: sender authentication and peer identity in §11.1,
state transitions (READY=1, RELOADING=1) and watchdog keepalives
(WATCHDOG=1, WATCHDOG_USEC) and timeout extension
(EXTEND_TIMEOUT_USEC) in §5.3, STOPPING=1 acknowledgement in
§10.1, fd store lifecycle (FDSTORE, FDNAME, FDSTOREREMOVE, FDPOLL)
in §11.1, and STATUS= exposure in §11.2.

`STATUS=`, `ERRNO=`, and `EXIT_STATUS=` are event-emitting fields:
peinit MUST authenticate the sender, then emit the value as a
structured KMES event (`kmes_emit`) whose msgpack payload carries
the service name and job GUID -- the same event path as job and
operation lifecycle events (§7.1, §8.1), not a forward to eventd.
`STATUS=` is additionally stored on the service's runtime state and
exposed via the `status_text` field in status query responses.
`ERRNO=` and `EXIT_STATUS=` are not stored -- they are emitted as
events and otherwise not retained. All three fields MUST be subject
to the same sender authentication as other sd_notify messages.

## Calendar expressions

Timer schedules use systemd's OnCalendar expression format:

```
DayOfWeek Year-Month-Day Hour:Minute:Second Timezone
```

Each field supports wildcards (`*`), lists (`1,15`), ranges
(`Mon..Fri`), repetition (`*-*-* *:0/15:00`), and last-day-of-month
counting (`Year-Month~Day`, where `~01` is the last day). Timezone
specifiers (e.g., `Europe/London`, `US/Eastern`) are supported;
expressions without a timezone are interpreted in system-local
time. systemd's named shortcuts (`minutely`, `hourly`, `daily`,
`weekly`, `monthly`, `quarterly`, `semiannually`,
`yearly`/`annually`) are supported.

DST transitions are handled as follows:

- **Spring forward** (clock skips an hour): scheduled times that
  fall within the skipped interval MUST NOT fire. The next valid
  occurrence fires normally.
- **Fall back** (clock repeats an hour): scheduled times that fall
  within the repeated interval MUST fire exactly once, on the first
  occurrence.

The exact parsing rules and next-occurrence computation are defined
in §9.1.

## systemd unit files

peinit does not read, parse, or translate systemd unit files.
Service definitions are stored in the registry under
`Machine\System\Services\`. There is no compatibility layer,
generator, or migration path at the init level. Role definitions
are the mechanism for declaring service configuration in Peios.

## Windows SCM

peinit's service model is influenced by Windows Service Control
Manager concepts: services as securable objects with per-service
Security Descriptors, token-based service identity, a control
interface with access-controlled operations, and a structured
service state machine. This influence is architectural, not
interface-level. peinit does not implement the Windows SCM RPC
protocol, Windows service types (kernel driver, shared process),
or Windows-specific control codes.

## Features handled by other subsystems

The following features relevant to a complete service management
posture are not part of peinit:

| Feature | Subsystem |
|---|---|
| Authentication and token minting | authd |
| Local identity database | lpsd |
| Log storage, indexing, and queries | eventd |
| Registry storage | registryd (via LCS) |
| Software packaging and installation | Role system, pacman |
| Device management | eudev |
| Network configuration | Dedicated network service |
| DNS, DHCP, and infrastructure services | Role-installed services |
| File access control enforcement | FACS |
