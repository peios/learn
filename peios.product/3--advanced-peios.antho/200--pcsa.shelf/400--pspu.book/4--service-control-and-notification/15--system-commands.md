---
title: System Commands
description: shutdown and reload-config — the two commands that act on the manager itself, and why reload is atomic but not a live update.
---

Two commands act on the manager rather than on a service.

## shutdown

```json
{"command": "shutdown", "type": "reboot"}
```

`type` MUST be one of:

| Value | Meaning |
|---|---|
| `poweroff` | Stop everything and remove power. |
| `reboot` | Stop everything and restart the machine. |
| `halt` | Stop everything and halt, leaving the machine powered. |

The response is `{"status": "ok"}` and nothing else. There is no
operation to observe: a shutdown is a mode the manager enters, not an
action on a service, and by the time it has finished there is nobody
left to tell.

A client MUST NOT expect the connection to survive. The manager MAY
close it at any point after the response.

## reload-config

Re-reads the configuration and rebuilds whatever the manager derives
from it.

```json
{
    "status": "ok",
    "summary": {
        "added": ["jellyfin"],
        "updated": ["sshd"],
        "restored": [],
        "marked_removed": ["old-migration"],
        "discarded": ["obsolete-timer"]
    },
    "warnings": []
}
```

| Field | Type | Meaning |
|---|---|---|
| `added` | array of strings | Services that did not exist before. |
| `updated` | array of strings | Services whose definition changed. |
| `restored` | array of strings | Services whose withdrawal was reversed. |
| `marked_removed` | array of strings | Services whose definition is gone but which are still running. |
| `discarded` | array of strings | Services removed outright. |
| `warnings` | array of strings | Human-readable warnings about the new configuration. |

Every member of `summary` MUST be present, even when empty. A client
MUST accept a member of `summary` it does not recognise, and MUST ignore
it (§4.21).

### It is atomic

The manager MUST validate the new configuration in full before adopting
any of it, and MUST adopt it only if validation succeeds. If validation
fails, the manager MUST leave the previous configuration in force and
MUST answer `INVALID_STATE`, reporting what was wrong.

A partially applied configuration is worse than the one already running:
the running one at least booted.

### It does not live-update

The manager MUST NOT reconfigure a running service. A changed definition
takes effect the next time that service starts.

## During shutdown

Once the manager is shutting down, it MUST reject every command except
`status`, `list`, `operation-status`, `job-status`, `job-list` and
`job-stop` with `INVALID_STATE`.

The first five are permitted because they change nothing and because a
client watching a shutdown proceed has a legitimate reason to keep
looking; `job-stop` because a job the shutdown will reach eventually
may be one a client has reason to end now. Everything else — including
a second `shutdown` — is refused:
the manager has committed to a course of action and a command that
would alter it arrives too late to be honoured consistently.

As §4.7 says, this restriction is evaluated before the access check, so
a caller who would have been denied receives `INVALID_STATE` instead.
