---
title: Protocol
---

## Control socket

peinit exposes a Unix stream socket at `/run/peinit/control.sock`
for runtime commands. The socket is created during Phase 1
infrastructure setup (after `/run` is mounted and registryd is
running) and exists for the lifetime of the system.

### Wire format

Messages are newline-delimited JSON. Each message is one JSON
object per line -- no pretty-printing. This eliminates ambiguity
about message boundaries.

**Request format:**

```json
{"command": "start", "service": "jellyfin", "wait": true}
```

**Success response:**

```json
{"status": "ok", "operation_id": "a1b2c3d4-...", "service": "jellyfin", "state": "active", "cause": "explicit_start", "warnings": []}
```

**Error response:**

```json
{"status": "error", "code": "ACCESS_DENIED", "message": "caller lacks SERVICE_START on jellyfin"}
```

Field names, types, and value formats in JSON examples throughout
this specification are normative.

### Error codes

The `code` field of an error response MUST be one of the following
canonical values. The `message` field is human-readable and
non-normative.

| Code | Meaning |
|---|---|
| `ACCESS_DENIED` | AccessCheck denied the command against the target SD. |
| `UNKNOWN_SERVICE` | The named service has no definition. |
| `UNKNOWN_OPERATION` | The operation GUID is not known -- it never existed, or was dropped after its retention grace (§8.1). |
| `MALFORMED_REQUEST` | The request line is not a single valid JSON object, or is not parseable. |
| `REQUEST_TOO_LARGE` | The request exceeds `MaxRequestSize`. |
| `INVALID_COMMAND` | The `command` field is missing or names no known command. |
| `INVALID_ARGUMENTS` | Required fields for the command are missing or malformed (e.g. `shutdown` without a valid `type`). |
| `INVALID_STATE` | The command is not valid for the service's current state -- the `ERROR` cells of the command x state matrix (§11.2). |
| `OPERATION_TIMEOUT` | A `wait=true` request's operation did not reach a terminal state within its timeout. |
| `INTERNAL_ERROR` | peinit encountered an internal failure while executing the command. |

Connections that exceed `MaxControlConnections` are rejected at the
socket level before any request is read; that rejection is a
connection close, not one of the error codes above.

### Peer authentication

When a client connects, peinit MUST obtain the caller's identity
via `kacs_open_peer_token` (KACS syscall). This returns a token fd
representing the peer's KACS identity. The kernel provides this --
there is no userspace credential exchange.

The token returned by `kacs_open_peer_token` is the peer thread's
effective token at connection time -- if the peer is impersonating,
the impersonation token is captured. This ensures that access
control decisions reflect the identity under which the client is
actually operating, not its underlying service identity. The exact
semantics of `kacs_open_peer_token` are defined in PSD-004.

For each command, peinit MUST call AccessCheck with:

- **Token:** the peer's token.
- **SD:** the target service's ServiceSecurity SD (for service
  commands) or peinit's control SD (for system commands).
- **Desired access:** the access right for the command.

If AccessCheck denies access, peinit MUST return an ACCESS_DENIED
error and log the attempt.

### Limits

peinit MUST enforce hard limits on the control socket:

| Registry key | Default | Description |
|---|---|---|
| `Machine\System\Init\MaxControlConnections` | 32 | Maximum concurrent client connections. |
| `Machine\System\Init\MaxRequestSize` | 65536 | Maximum request size in bytes. |
| `Machine\System\Init\ConnectionTimeout` | 30 | Seconds before an idle connection is closed. |

Connections exceeding MaxControlConnections MUST be rejected.
Requests exceeding MaxRequestSize MUST be rejected. Idle
connections exceeding ConnectionTimeout MUST be closed.

A connection is "idle" only when it has no in-flight request. A
connection blocked awaiting completion of a `wait=true` operation
MUST NOT be treated as idle, even when the operation runs longer
than ConnectionTimeout. peinit MUST keep such a connection open
until the operation resolves, bounded by the operation's own
timeout (e.g. StartTimeout) rather than ConnectionTimeout.

## Notify socket

peinit creates a Unix datagram socket for sd_notify messages. The
path is an internal implementation detail -- services receive it
via the `NOTIFY_SOCKET` environment variable set during pre-exec.
No service hardcodes the path.

### Sender authentication

peinit MUST authenticate sd_notify senders:

1. Enable `SO_PASSCRED` on the notify socket.
2. Receive the sender's PID via `SCM_CREDENTIALS`
   (kernel-attested).
3. Validate the PID against the service's tracked main PID
   (verified via pidfd). NotifyAccess=Main is the only supported
   mode.
4. Validate the start generation -- messages from a previous
   incarnation MUST be rejected.

Messages from unrecognised senders MUST be dropped and logged.
UID/GID from `SCM_CREDENTIALS` are not policy inputs.

## Fd store

The fd store allows a service to persist file descriptors across
restarts. A service pushes fds to peinit via sd_notify; peinit
holds them and re-injects them into the new process on restart.
This enables stateful daemons (e.g., a web server preserving
listening sockets) to restart without dropping connections.

### Schema control

The FdStoreMax field in the service definition (default 0)
controls the maximum number of file descriptors peinit will hold
for the service. When FdStoreMax is 0, the fd store is disabled
-- FDSTORE=1 messages are logged and the accompanying fd is
closed.

### Storing an fd

When a service sends an sd_notify message containing `FDSTORE=1`
with a file descriptor attached via `SCM_RIGHTS`:

1. peinit MUST authenticate the sender using the same PID-matching
   and generation validation as all other sd_notify messages (see
   Sender authentication above).
2. If the service's FdStoreMax is 0, peinit MUST log the rejection
   and close the received fd.
3. If the fd store already contains FdStoreMax entries, peinit MUST
   log the rejection and close the received fd. The existing store
   is not modified.
4. If `FDNAME=<name>` is present in the message, the fd is stored
   under that name. If FDNAME is absent, the fd is stored under the
   default name `"stored"`.
5. If `FDPOLL=0` is present, peinit MUST mark the fd as exempt from
   poll monitoring. By default, peinit MAY monitor stored fds for
   error conditions (POLLERR, POLLHUP) and remove fds that become
   invalid.

Multiple fds MAY share the same name. On injection, all fds with
a given name appear in LISTEN_FDNAMES in storage order.

### Removing an fd

When a service sends an sd_notify message containing
`FDSTOREREMOVE=1` with `FDNAME=<name>`:

1. peinit MUST authenticate the sender.
2. peinit MUST remove all stored fds matching the given name and
   close them.
3. If no fd with the given name exists, the message is a no-op.
   peinit MUST NOT treat this as an error.

### Injection on restart

When a service restarts (transitions from a failed or stopping
state back to Starting), peinit MUST inject stored fds into the
new process during child pre-exec (Step 8 of the Pre-Exec
Sequence):

1. Stored fds are passed as inherited file descriptors starting at
   `SD_LISTEN_FDS_START` (file descriptor 3).
2. The `LISTEN_FDS` environment variable MUST be set to the number
   of injected fds.
3. The `LISTEN_FDNAMES` environment variable MUST be set to a
   colon-separated list of fd names, in the same order as the fd
   numbers.
4. After successful injection, the fd store is cleared -- peinit no
   longer holds the fds.

### Clearing the fd store

The fd store MUST be cleared (all stored fds closed) in the
following situations:

- **Explicit stop:** when a service is stopped by an administrator
  or by shutdown (not a crash-triggered restart). The fds are no
  longer useful -- the service is not coming back.
- **Service removal:** when a service definition is removed and its
  entry is finally discarded -- immediately if the service was not
  running, or on the running instance's exit otherwise (§3.5). All
  associated state, including stored fds, is discarded at that
  point.

The fd store survives across automatic restarts (crash -> restart
policy -> new start). This is the entire point of the mechanism --
fds persist through the restart that the service cannot control.

> [!INFORMATIVE]
> The fd store is a targeted mechanism for socket activation and
> graceful restart scenarios. Most services do not need it --
> FdStoreMax defaults to 0 for this reason. Services that use it
> must be designed to receive and re-use inherited fds. The
> LISTEN_FDS / LISTEN_FDNAMES interface is the same convention used
> by systemd's fd store, so existing software that supports
> systemd fd passing works without modification.

## Outbound IPC

peinit connects to three services:

| Service | Purpose | Protocol | Failure behaviour |
|---|---|---|---|
| registryd | Service definitions, boot settings. | LCS syscalls (boot); in-memory cache + change notifications (runtime). | Phase 1: recovery mode. Runtime: operates on cached model. |
| authd | Service tokens. | JSON over Unix stream socket (non-blocking, state-machine driven with timeout). Provisional -- wire schema, socket path, and fd-passing are deferred to the authd spec (§3.3). | Non-SYSTEM services cannot start. Platform services unaffected. |
| eventd | Forward service stdout/stderr (logs only). | msgpack over a Unix **datagram** socket at `Machine\System\eventd\LogSocketPath` (non-blocking, loss-tolerant). | Logs buffered pre-eventd, then best-effort replayed. Datagrams may drop under load -- no backpressure. |

All outbound IPC MUST be non-blocking. authd uses a Unix stream
socket with epoll; eventd's log socket is a Unix datagram socket.
Token requests to authd are state-machine driven with timeouts --
if authd is unresponsive, the service start fails rather than PID 1
hanging.

Structured events (job and operation lifecycle, audit records) are
NOT sent over any of these sockets. peinit emits them via the KMES
`kmes_emit` / `kmes_emit_batch` syscalls into the kernel ring
buffer, whence eventd consumes them. KMES is the sole event path
(PSD-003) -- there is no event socket to eventd.
