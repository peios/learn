---
title: Authorising a Command
description: Every command is checked against a Security Descriptor using the peer's token — the rights, the per-command mapping, and why some results are filtered rather than denied.
---

Every command is authorised against a Security Descriptor, using the
peer's token. There is no command the manager performs without a check,
and no principal exempt from one.

## Rights

Commands acting on a service are checked against that service's
descriptor:

| Right | Bit | Grants |
|---|---|---|
| `SERVICE_QUERY_STATUS` | 0x0001 | Query the service's state and detail. |
| `SERVICE_START` | 0x0002 | Start the service. |
| `SERVICE_STOP` | 0x0004 | Stop the service. |
| `SERVICE_INTERROGATE` | 0x0008 | Reload the service. |
| `SERVICE_ALL_ACCESS` | 0x000F | All four. |

Commands acting on the system are checked against the manager's own
descriptor:

| Right | Bit | Grants |
|---|---|---|
| `SYSTEM_SHUTDOWN` | 0x0001 | Initiate a shutdown. |
| `SYSTEM_RELOAD_CONFIG` | 0x0002 | Re-read the configuration. |

## Generic mappings

The manager MUST use these generic mappings when evaluating a
descriptor, so that a descriptor written in generic terms means the same
thing to every implementation.

For a service descriptor:

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `SERVICE_QUERY_STATUS` |
| `GENERIC_WRITE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_EXECUTE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_ALL` | `SERVICE_ALL_ACCESS` |

For the manager's descriptor:

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | 0 |
| `GENERIC_WRITE` | `SYSTEM_RELOAD_CONFIG` |
| `GENERIC_EXECUTE` | `SYSTEM_SHUTDOWN` |
| `GENERIC_ALL` | `SYSTEM_SHUTDOWN` \| `SYSTEM_RELOAD_CONFIG` |

`GENERIC_READ` maps to nothing on the manager's descriptor because it
governs two actions and no queries.

## Per command

| Command | Right required |
|---|---|
| `start` | `SERVICE_START` |
| `stop` | `SERVICE_STOP` |
| `restart` | `SERVICE_START` and `SERVICE_STOP` |
| `reload` | `SERVICE_INTERROGATE` |
| `reset` | `SERVICE_STOP` |
| `status` | `SERVICE_QUERY_STATUS` |
| `list` | Evaluated per service; see below |
| `operation-status` | `SERVICE_QUERY_STATUS` on the operation's target |
| `shutdown` | `SYSTEM_SHUTDOWN` |
| `reload-config` | `SYSTEM_RELOAD_CONFIG` |

`reset` requires `SERVICE_STOP` because clearing a terminal state is the
tail of stopping something rather than the head of starting it.

## The sequence

1. If the manager is shutting down, apply §4.15's restriction. The
   shutdown restriction is evaluated **before** the access check, so a
   caller who would have been denied is told the command is invalid for
   the current state. A client MUST NOT infer anything about its own
   rights from an `INVALID_STATE` received during shutdown.
2. Resolve the target. A command naming no service the manager knows of
   MUST be answered `UNKNOWN_SERVICE`. The manager MUST NOT synthesise a
   descriptor for a service that does not exist.
3. Evaluate the access check with the peer's token, the target's
   descriptor, the appropriate generic mapping, and the required right.
4. On denial, answer `ACCESS_DENIED`, and record the attempt with at
   least the caller's SID, the target, and the right requested. The
   manager MUST NOT deny silently.
5. On grant, proceed.

## Filtering rather than denying

`list` MUST return only the services the caller may query, and MUST
**omit** the rest rather than denying the command. A caller with no
query rights on anything receives an empty list and a successful
response.

The manager MUST NOT reveal, through the response, that services were
omitted. Reporting the omissions would answer the question the filtering
exists to leave unanswered.

## Not revealing what a caller may not see

Where a command names an object the caller may not query,
the manager MUST NOT let the answer distinguish "this does not exist"
from "you may not see this".

For `operation-status` this means the authorisation check MUST be
evaluated before the operation's existence is reported: a caller lacking
`SERVICE_QUERY_STATUS` on an operation's target MUST receive
`ACCESS_DENIED` whether or not the identifier names a real operation,
and MUST NOT receive `UNKNOWN_OPERATION` for one that exists.

Where the caller's rights cannot be established because the target
cannot be resolved, `UNKNOWN_OPERATION` is the correct answer.
