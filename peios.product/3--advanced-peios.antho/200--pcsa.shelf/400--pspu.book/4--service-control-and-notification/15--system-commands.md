---
title: System Commands
description: shutdown, reload-config and boot — the commands that act on or ask about the manager itself, why reload is atomic but not a live update, and what boot reports.
---

Three commands are about the manager rather than a service. Two act on
it; the third, `boot`, asks how the machine booted.

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

## boot

Reports how the current boot went: which mode the machine booted in and
why, how close it is to recovery, and whether this boot has counted as a
successful one yet. It takes no arguments and changes nothing.

```json
{"command": "boot"}
```

A **boot mode** is how much of the configuration a boot starts. In
`full` mode the manager starts everything configured to start at boot.
In `safe` mode it starts a reduced set: the services the boot cannot do
without, which this chapter calls **critical services**, and those
marked as wanted in Safe mode. In `recovery` mode it starts nothing and
offers a maintenance shell instead. Which services are critical, and
what each mode starts, is the manager's design.

A boot is **confirmed** once it has shown it works: every critical
service has held a dependent-satisfying state (§4.2) for a **grace
period** without a break. The manager keeps a **boot attempt count**,
the number of boots in a row that started and were never confirmed, and
enters recovery when it reaches a **threshold** rather than boot into
the same failure again. Confirming a boot puts the count back to 0.

```json
{
    "status": "ok",
    "boot": {
        "mode": "safe",
        "reason": "safe_mode_downgrade",
        "downgrade": ["critical service in dependency cycle storage -> network"],
        "attempts": 1,
        "max_attempts": 3,
        "confirmed": false,
        "grace_seconds": 30,
        "waiting_on": ["storage"],
        "confirms_at": null,
        "confirm_error": null
    }
}
```

| Field | Type | Meaning |
|---|---|---|
| `mode` | string | The mode the machine booted in, after any downgrade. §4.B |
| `reason` | string | Why it is in that mode. §4.B |
| `downgrade` | array of strings | What forced a downgrade, one human-readable finding each. Empty unless `reason` is `safe_mode_downgrade`. |
| `attempts` | integer | The boot attempt count as the manager checked it against the threshold at the start of this boot. |
| `max_attempts` | integer | The threshold. 0 means the check is off and the count never sends the machine to recovery. |
| `confirmed` | bool | This boot has been confirmed, and the count has been put back to 0. |
| `grace_seconds` | integer | The grace period, in seconds. |
| `waiting_on` | array of strings | The critical services not yet holding a dependent-satisfying state. Empty once the grace period has ended. |
| `confirms_at` | string or null | When the boot will be confirmed if every critical service keeps holding, in RFC 3339 UTC. Null while `waiting_on` is not empty, and once the grace period has ended. |
| `confirm_error` | string or null | Why the count could not be put back to 0 when the grace period ended. Human-readable. |

Every member of `boot` MUST be present. A client MUST accept a member of
`boot` it does not recognise, and MUST ignore it (§4.21).

`attempts` counts the boots before this one; this boot is not among
them. A machine reaches recovery when a boot begins with `attempts` at
or above `max_attempts`, so `max_attempts - attempts` is how many more
unconfirmed boots the machine has before recovery.

`confirmed` MUST be true only once the count has actually been put back
to 0. If the grace period ended but the manager could not write the
count, `confirmed` is false and `confirm_error` says why: the next boot
will count this one as a failed attempt, whatever its services did, and
a client MUST NOT report the boot as confirmed.

A confirmed boot stays confirmed. A critical service that fails after
confirmation is a failure of that service, not of the boot, and does not
make `confirmed` false again.

A manager in `recovery` mode does not serve the control channel, so a
client SHOULD NOT expect to read `recovery` from `boot`; the value
exists so that a manager which does serve it there has a word for it.

`boot` is checked against the manager's descriptor for
`SYSTEM_QUERY_STATUS` (§4.7). How a machine booted is not a secret, and
a manager's default descriptor SHOULD grant this right to every
authenticated principal.

## During shutdown

Once the manager is shutting down, it MUST reject every command except
`status`, `list`, `operation-status`, `boot`, `job-status`, `job-list`
and `job-stop` with `INVALID_STATE`.

The first six are permitted because they change nothing and because a
client watching a shutdown proceed has a legitimate reason to keep
looking; `job-stop` because a job the shutdown will reach eventually
may be one a client has reason to end now. Everything else — including
a second `shutdown` — is refused:
the manager has committed to a course of action and a command that
would alter it arrives too late to be honoured consistently.

As §4.7 says, this restriction is evaluated before the access check, so
a caller who would have been denied receives `INVALID_STATE` instead.
