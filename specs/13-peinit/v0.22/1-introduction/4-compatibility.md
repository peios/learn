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
environment variable. peinit authenticates senders via kernel-
attested PID matching.

The following sd_notify fields are supported:

| Field | Behaviour |
|---|---|
| `READY=1` | Service has completed startup and is ready to serve. Gates dependent startup for services using Notify readiness. |
| `RELOADING=1` | Service is reloading configuration. Extends the reload detection window so peinit waits for `READY=1` completion (see the Restart and Reload section). |
| `STOPPING=1` | Service is shutting down gracefully. Acknowledged by peinit. |
| `STATUS=...` | Human-readable status string. Forwarded to eventd and exposed via status queries. |
| `ERRNO=...` | Errno-style error number. Forwarded to eventd. |
| `EXIT_STATUS=...` | Exit status for informational purposes. Forwarded to eventd. |
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

The exact semantics of each field are defined in their respective
sections: sender authentication and peer identity in the Control
Interface section, state transitions (READY=1, RELOADING=1) and
watchdog keepalives (WATCHDOG=1, WATCHDOG_USEC) and timeout
extension (EXTEND_TIMEOUT_USEC) in the Restart and Reload
section, STOPPING=1 acknowledgement in the Shutdown section, fd
store lifecycle (FDSTORE, FDNAME, FDSTOREREMOVE, FDPOLL) in the
Control Interface section, and STATUS= exposure in the Command
Set section.

`STATUS=`, `ERRNO=`, and `EXIT_STATUS=` are forwarding fields:
peinit MUST authenticate the sender, then forward the value to
eventd as a structured event tagged with the service name and job
GUID. `STATUS=` is additionally stored on the service's runtime
state and exposed via the `status_text` field in status query
responses. `ERRNO=` and `EXIT_STATUS=` are not stored -- they
are forwarded to eventd and discarded. All three fields MUST be
subject to the same sender authentication as other sd_notify
messages.

## Calendar expressions

Timer schedules use systemd's OnCalendar expression format:

```
DayOfWeek Year-Month-Day Hour:Minute:Second Timezone
```

Each field supports wildcards (`*`), lists (`1,15`), ranges
(`Mon..Fri`), repetition (`*-*-* *:00/15:00`), and last-day-of-
month (`~`). Timezone specifiers (e.g., `Europe/London`,
`US/Eastern`) are supported; expressions without a timezone are
interpreted in system-local time. The shortcuts `daily`, `hourly`,
`weekly`, and `monthly` are supported.

DST transitions are handled as follows:

- **Spring forward** (clock skips an hour): scheduled times that
  fall within the skipped interval MUST NOT fire. The next valid
  occurrence fires normally.
- **Fall back** (clock repeats an hour): scheduled times that fall
  within the repeated interval MUST fire exactly once, on the first
  occurrence.

The exact parsing rules and next-occurrence computation are defined
in the Timers section.

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
