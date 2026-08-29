---
title: Errors
description: The closed set of error codes a manager may emit, the distinctions a client can rely on, and why the set cannot grow without a version bump.
---

The `code` field of an error response MUST be one of these values. The
manager MUST NOT emit any other code, and a client MUST treat a code it
does not recognise as an unrecoverable error for that request (§4.21).

| Code | Meaning | Closes? |
|---|---|---|
| `MALFORMED_REQUEST` | The frame is not a single well-formed JSON object. §4.5 | On an empty frame |
| `REQUEST_TOO_LARGE` | The request exceeds the configured maximum. §4.4 | Yes |
| `INVALID_COMMAND` | `command` is absent, not a string, or names no known command. | No |
| `INVALID_ARGUMENTS` | A field the command requires is absent or malformed. | No |
| `UNKNOWN_SERVICE` | The named service has no definition the manager can act on. | No |
| `UNKNOWN_OPERATION` | The operation identifier names nothing the manager holds — it never existed, or its retention has elapsed. §4.14 | No |
| `UNKNOWN_JOB` | The job identifier names nothing the manager holds — it never existed, or its retention has elapsed. §7.7 | No |
| `ACCESS_DENIED` | The access check denied the requested right. §4.7 | No |
| `INVALID_STATE` | The command is not valid for the service's current state (§4.12), or the manager is shutting down (§4.15). | No |
| `OPERATION_TIMEOUT` | A `wait=true` request's operation did not reach a terminal state in time. §4.13 | No |
| `INTERNAL_ERROR` | The manager failed while executing the command. | No |

## Distinctions a client can rely on

**`UNKNOWN_SERVICE` versus `ACCESS_DENIED`.** A caller that may not
query a service still receives `UNKNOWN_SERVICE` for a name that does
not exist and `ACCESS_DENIED` for one that does but which it may not
touch. This chapter does not attempt to hide the existence of services
from a caller that can name them: the `list` filtering (§4.7) hides them
from a caller that cannot.

**`INVALID_STATE` versus `ACCESS_DENIED` during shutdown.** During
shutdown the state restriction is evaluated first, so a caller who would
have been denied receives `INVALID_STATE` instead. A client MUST NOT
infer that it holds a right from receiving `INVALID_STATE`.

**`OPERATION_TIMEOUT` does not cancel anything.** It reports that the
client's wait ended, not that the operation did. The operation continues
and can still be observed with `operation-status`.

## Codes are not extensible without a version

The manager MUST NOT introduce a new code without the version negotiation
in §4.21. A client written against this revision will not recognise one,
and the only safe thing it can do with an unrecognised code is fail the
request — so a new code silently converts a handled condition into an
unhandled one.
