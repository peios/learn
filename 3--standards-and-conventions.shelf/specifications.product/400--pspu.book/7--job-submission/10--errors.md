---
title: Errors
description: The closed set of error codes the jobs channel may emit — §4.10's, less those that cannot arise here, plus three of its own.
---

The `code` field of an error response MUST be one of these values. The
manager MUST NOT emit any other code on this channel, and a submitter
MUST treat a code it does not recognise as an unrecoverable error for
that request (§7.11).

| Code | Meaning | Closes? |
|---|---|---|
| `MALFORMED_REQUEST` | The message is not a single well-formed JSON object. §7.4 | No |
| `REQUEST_TOO_LARGE` | The message exceeds the configured maximum, or was truncated. §7.3 | Yes |
| `INVALID_COMMAND` | `command` is absent, not a string, or names no command. | No |
| `INVALID_ARGUMENTS` | A field is absent, malformed, or inconsistent with the attachments. §7.6, §7.9 | No |
| `UNKNOWN_JOB` | `job_id` names nothing the manager holds — it never existed, or its retention has elapsed. §7.7 | No |
| `ACCESS_DENIED` | The access check against the job's descriptor denied the right. §7.8 | No |
| `INVALID_STATE` | The command is not valid for the job's state, or the manager is shutting down. | No |
| `QUOTA_EXCEEDED` | The submitter already holds its maximum of live jobs. §7.3 | No |
| `BAD_TOKEN` | The attached token cannot be a job identity. §7.5 | No |
| `INTERNAL_ERROR` | The manager failed while executing the command. | No |

`UNKNOWN_SERVICE`, `UNKNOWN_OPERATION` and `OPERATION_TIMEOUT` are
not emitted here: nothing on this channel names a service or an
operation, and a `wait` has no timeout of its own to expire.

## Distinctions a submitter can rely on

**`UNKNOWN_JOB` versus `ACCESS_DENIED`.** A caller that may not query a
job receives `ACCESS_DENIED` for an identifier that exists, and
`UNKNOWN_JOB` for one that does not. This channel does not hide the
existence of a job from a caller that can name it: identifiers are
unguessable, and a caller that holds one was told it by something that
had it.

**`BAD_TOKEN` is about the token, never about the identity.** It says
the attached token is unusable — its level, its count, its rights —
and never that the submitter may not act as the principal it names.
That decision was the kernel's, made before the message arrived, and a
submitter that could not convey an identity never reaches the manager
with it.

**`QUOTA_EXCEEDED` created nothing.** No record, no event, no
consumption. A submitter MAY retry once one of its live jobs ends.

**`INVALID_STATE` during shutdown.** Once the manager is shutting
down it MUST reject `submit` with `INVALID_STATE` and MUST continue to
answer `status`, `wait`, `stop` and `signal`; a submitter watching its
jobs be stopped has a legitimate reason to keep looking, and a
submitter that wants a job stopped sooner than the shutdown will
manage has a legitimate reason to ask.

## Codes are not extensible without a version

The manager MUST NOT introduce a new code without the negotiation in
§4.21, for the reason §4.10 gives: an unrecognised code silently turns
a handled condition into an unhandled one.
