---
title: Controlling services
type: reference
description: peiosctl and the control socket — the verbs and their rights, wait semantics, the command-by-state matrix, status output, and error codes.
related:
  - peios/services-and-jobs/the-service-lifecycle
  - peios/services-and-jobs/who-can-manage-a-service
  - peios/services-and-jobs/jobs-and-operations
  - peios/services-and-jobs/shutdown
  - peios/services-and-jobs/troubleshooting
---

`peiosctl` is the command-line tool for driving **peinit** at runtime — starting and stopping services, querying their state, reloading configuration, and shutting the system down.

```
peiosctl <command> [service] [flags]
```

```
$ peiosctl status jellyfin        # current state of one service
$ peiosctl start jellyfin         # start it, wait until Active or Failed
$ peiosctl list                   # every service you can query
$ peiosctl shutdown reboot        # graceful reboot
```

Underneath, `peiosctl` is a thin client over peinit's **control socket** at `/run/services/peinit/control.sock`. The wire protocol — not the CLI — is the normative interface, so everything here (commands, rights, semantics) holds regardless of which front-end you use.

## How the control interface works

The socket speaks **newline-delimited JSON**: one request object per line, one response object per line. A request and its success response look like this:

```json
{"command": "start", "service": "jellyfin", "wait": true}
{"status": "ok", "operation_id": "a1b2c3d4-...", "service": "jellyfin", "state": "active", "cause": "explicit_start", "warnings": []}
```

Two properties are worth knowing even if you only ever use `peiosctl`:

- **Every command is access-controlled.** When you connect, peinit captures your [token](~peios/services-and-jobs/identity-and-privileges) from the kernel and runs [AccessCheck](~peios/access-decisions/overview) against the target service's descriptor for *every* command. There is no "trust localhost," no override. Who may do what is the subject of [Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service).
- **Lifecycle commands create [operations](~peios/services-and-jobs/jobs-and-operations).** A `start`/`stop`/`restart`/`reload`/`reset` returns an `operation_id` — a GUID you can poll. Conflict resolution between concurrent commands happens at the operation layer, which is why two simultaneous `start`s merge instead of colliding.

## Service commands

| Command | Does | Required right |
|---|---|---|
| `start` | Run the service through its full start sequence. | `SERVICE_START` |
| `stop` | SIGTERM, then SIGKILL after `StopTimeout`. | `SERVICE_STOP` |
| `restart` | Stop then start, as one operation. | `SERVICE_STOP` + `SERVICE_START` |
| `reload` | Re-read configuration (`ExecReload`, or SIGHUP). | `SERVICE_INTERROGATE` |
| `reset` | Clear `Failed`/`Abandoned`/`Skipped` → `Inactive`. | `SERVICE_STOP` |
| `status` | Report state, cause, PID, uptime, health, current job and operation, warnings. | `SERVICE_QUERY_STATUS` |
| `list` | List services and states (filtered to what you can query). | (per-service `SERVICE_QUERY_STATUS`) |

```
$ peiosctl restart jellyfin
$ peiosctl reload nginx
$ peiosctl reset failed-migration     # clear a Failed state without starting
```

## System commands

| Command | Does | Required right |
|---|---|---|
| `shutdown <type>` | Graceful [shutdown](~peios/services-and-jobs/shutdown). `type` is `poweroff`, `reboot`, or `halt`. | `SYSTEM_SHUTDOWN` |
| `reload-config` | Re-read *all* definitions and rebuild the graph (atomic). | `SYSTEM_RELOAD_CONFIG` |
| `operation-status <id>` | Report the state of an operation by GUID. | `SERVICE_QUERY_STATUS` on its target |

```
$ peiosctl shutdown poweroff
$ peiosctl reload-config
$ peiosctl operation-status a1b2c3d4-...
```

## Wait semantics

By default, a lifecycle command **blocks until its operation reaches a terminal state** — `start` waits for Active (or Failed), `stop` waits for Inactive, and so on. Pass `--no-wait` to get the `operation_id` back immediately and poll with `operation-status` instead.

| Command | Default | Waits for |
|---|---|---|
| `start` | wait | Active (Simple) / Completed or Inactive (Oneshot), or Failed |
| `stop` | wait | Inactive |
| `restart` | wait | the successful start target, or Failed |
| `reload` | **no-wait** | (with `--wait`) the Reloading state to resolve |
| `reset` | immediate | — |

`reload` is the exception — it returns immediately by default, because a reload may have no observable completion. With `--wait`, the response carries a `mode`:

| `mode` | Meaning |
|---|---|
| `confirmed` | The service signalled `READY=1` (and, for a command reload, the command exited 0). |
| `advisory` | The reload was issued and the detection window elapsed without explicit confirmation. |
| `failed` | The `ExecReload` command exited non-zero or timed out. **The service stays Active** — a failed reload never takes down a running service. |

The detection window is a **fixed 2 seconds** — it is built in and is *not* configurable via the registry. If the service says nothing within that window, the reload resolves as `advisory` and the service stays Active.

> [!NOTE]
> A connection blocked on a `--wait` operation is *not* counted as idle, so it is not closed by `ConnectionTimeout`. It stays open until the operation resolves, bounded by the operation's own timeout (e.g. `StartTimeout`).

## The command × state matrix

A command sent to a service in an unexpected state returns an **error**, not a silent no-op. This matrix is the authority on what each command does in each [state](~peios/services-and-jobs/the-service-lifecycle):

| Command | Inactive | Starting | Active | Reloading | Stopping | Completed | Backoff | Failed | Abandoned | Skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| **start** | Start | MERGE | ALREADY | ALREADY | QUEUE | Start | DEFER | Start | ERROR | Start |
| **stop** | NOOP | Cancel+Stop | Stop | Stop | MERGE | Clear | Cancel | NOOP | ERROR | NOOP |
| **restart** | Start | QUEUE | Restart | Restart | QUEUE | Start | Restart | Start | ERROR | Start |
| **reload** | ERROR | ERROR | Reload | MERGE | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| **reset** | NOOP | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | Clear | Clear | Clear |
| **status** | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |

Legend:

- **MERGE** — an operation of this type is already running; your command merges into it and you get its GUID.
- **DEFER** — your `start` is accepted and creates a Pending start operation, but it does *not* run yet: it waits out the service's existing backoff deadline and then starts. If a deferred start is already waiting, you merge into it and get its GUID.
- **ALREADY** — already in the target state; returns the current status, not an error.
- **QUEUE** — queued as Pending; runs after the current operation finishes.
- **NOOP** — no effect; returns the current status.
- **Clear** / **Cancel** — clear the state to Inactive / abort the current operation, then proceed.
- **ERROR** — invalid for this state; returns an error with an explanation.

The [Backoff](~peios/services-and-jobs/the-service-lifecycle) column is the subtle one: the service is down with an automatic restart pending, so `start` is *deferred* — it creates a Pending start that honours the remaining backoff delay and only runs once that deadline expires (a second `start` merges into the one already waiting), `stop` cancels the pending restart and any deferred start (the service goes Inactive), `restart` cancels the automatic one and does an admin restart, and `reload`/`reset` are invalid because no process exists.

## Reading status

`status` returns the full picture for one service:

```json
{
    "status": "ok",
    "service": "jellyfin",
    "state": "active",
    "cause": "explicit_start",
    "status_text": "Listening on port 8096",
    "current_job": {"id": "a1b2...", "type": "service_main", "pid": 1234, "started_at": "...", "identity": "jellyfin-svc"},
    "current_operation": {"id": "e5f6...", "type": "start", "source": "admin"},
    "health": "healthy",
    "uptime_seconds": 86400,
    "definition_removed": false,
    "warnings": []
}
```

- `state` and `cause` are the [lifecycle](~peios/services-and-jobs/the-service-lifecycle) pair — read them together.
- `status_text` is the latest `STATUS=` string the service sent via sd_notify (`null` if never sent; cleared on each restart).
- `current_job` and `current_operation` are the [job and operation](~peios/services-and-jobs/jobs-and-operations) GUIDs, or `null`.
- `health` is `healthy`, `unhealthy`, `unknown`, or `null` (no health check).
- `definition_removed` is `true` when the definition was deleted but an instance is still [draining](~peios/services-and-jobs/defining-a-service).
- `warnings` lists leaked sub-cgroups and other operator-relevant notices.

`list` returns a compact summary of every service you can query — services you lack `SERVICE_QUERY_STATUS` on are simply **omitted**, not denied:

```json
{"status": "ok", "services": [
    {"service": "jellyfin", "state": "active", "cause": "explicit_start", "health": "healthy"},
    {"service": "registryd", "state": "active", "cause": "dependency_start", "health": null}
]}
```

`operation-status` returns one operation by GUID; an unknown or expired GUID is the `UNKNOWN_OPERATION` error. (Operations are dropped after a short retention grace once terminal — long enough for a polling client to read the result, not forever.)

## Error codes

An error response is `{"status": "error", "code": "...", "message": "..."}`. The `code` is one of:

| Code | Meaning |
|---|---|
| `ACCESS_DENIED` | AccessCheck denied the command against the target descriptor. |
| `UNKNOWN_SERVICE` | No such service definition (also returned for `start`/`restart`/`reload` on a [definition-removed](~peios/services-and-jobs/defining-a-service) service). |
| `UNKNOWN_OPERATION` | No such operation GUID — never existed, or dropped after its retention grace. |
| `MALFORMED_REQUEST` | The request line is not a single valid JSON object. |
| `REQUEST_TOO_LARGE` | The request exceeds `MaxRequestSize`. |
| `INVALID_COMMAND` | The `command` field is missing or unknown. |
| `INVALID_ARGUMENTS` | A required field is missing or malformed (e.g. `shutdown` with no valid `type`). |
| `INVALID_STATE` | Not valid for the service's current state (an `ERROR` cell above), or rejected because the system is already shutting down. |
| `OPERATION_TIMEOUT` | A `--wait` operation did not reach a terminal state within its timeout. |
| `INTERNAL_ERROR` | peinit hit an internal failure executing the command. |

The `message` is human-readable and non-normative — read it for context, key off the `code`.

## Connection limits

peinit enforces hard limits on the control socket, all tunable under `Machine\System\Init\`:

| Key | Default | Limits |
|---|---|---|
| `MaxControlConnections` | 32 | Concurrent client connections (excess are refused at connect). |
| `MaxRequestSize` | 65536 | Bytes per request. |
| `ConnectionTimeout` | 30 | Seconds an *idle* connection may sit before it is closed. |

## Exit status

| Code | Meaning |
|---|---|
| `0` | The command succeeded. |
| `1` | A usage error. |
| non-zero | The command failed — an access denial, unknown service, invalid state, or timeout. |

## Where to start

To understand the states the matrix refers to, read [The service lifecycle](~peios/services-and-jobs/the-service-lifecycle).

To understand the operations every lifecycle command creates and how to poll them, read [Jobs and operations](~peios/services-and-jobs/jobs-and-operations).

To configure who may run each command, read [Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service).
