---
title: Requests
description: The fields a request JSON object carries, which apply to which commands, and the rules service names must satisfy.
---

A request is one JSON object.

```json
{"command": "start", "service": "jellyfin", "wait": true}
```

## Fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `command` | string | always | The command to run. §4.11, §4.14, §4.15 |
| `service` | string | for service commands | The target service's name. |
| `wait` | bool | no | Whether to block until the operation resolves. §4.13 |
| `type` | string | for `shutdown` | `poweroff`, `reboot` or `halt`. |
| `operation_id` | string | for `operation-status` | The operation to report on. |

`command` MUST be present and MUST be a string naming a command the
manager implements. A request whose `command` is absent, is not a
string, or names no known command MUST be answered `INVALID_COMMAND`.

`service` MUST be present and a string for `start`, `stop`, `restart`,
`reload`, `reset` and `status`. Its absence, or a non-string value, MUST
be answered `INVALID_ARGUMENTS`.

`wait` MUST be a boolean when present. A non-boolean MUST be answered
`INVALID_ARGUMENTS`. Its default is per command (§4.13).

`type` MUST be present and MUST be exactly one of the three values for
`shutdown`. Anything else MUST be answered `INVALID_ARGUMENTS`.

`operation_id` MUST be present and a string for `operation-status`. A
value that is not a well-formed identifier MUST be answered
`INVALID_ARGUMENTS`.

## Fields that do not apply

A field the command does not use MUST be ignored, not rejected. A
`service` on a `list`, or a `wait` on a `status`, is accepted and has no
effect.

This is what makes the request shape extensible: a client written
against a later revision may send a field an earlier manager does not
know, and the earlier manager ignores it. §4.21.

## Service names

A service name is 1 to 128 bytes drawn from `[A-Za-z0-9._-]`. The
manager MUST NOT accept a name outside that set, and a client MUST NOT
send one.

The restriction exists because service names are used as path
components and as configuration key names by managers that store their
definitions in a hierarchy. `/` and `:` are excluded specifically:
the first because it is a separator wherever the name is used as a path
component, and the second because it is conventionally reserved for a
manager's own synthetic naming.
