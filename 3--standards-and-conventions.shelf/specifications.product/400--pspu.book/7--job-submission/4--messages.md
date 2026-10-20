---
title: Messages
description: One compact JSON object per sequenced-packet message, in both directions, with a token and descriptors carried as ancillary data — and what is malformed.
---

## Content

Every message in both directions carries exactly one JSON object,
serialised compactly, as the whole of the record's content. There is
no terminator: the transport delimits messages, and the manager MUST
NOT require or emit a trailing newline.

Content is UTF-8. The manager MUST reject content that is not
well-formed UTF-8 with `MALFORMED_REQUEST`.

The rules of §4.5 for what is malformed apply unchanged: an empty
message, content that is not valid JSON, and valid JSON that is not an
object are all `MALFORMED_REQUEST`. The manager MUST NOT emit
pretty-printed JSON. Timestamps follow §4.5.

## Attachments

A request MAY carry ancillary data. Two kinds are defined:

| Level | Type | Meaning | Applies to |
|---|---|---|---|
| `SOL_KACS` | `KACS_SCM_TOKEN` | The token the job is to run as. At most one. | `submit` |
| `SOL_SOCKET` | `SCM_RIGHTS` | Descriptors for the job, or an output sink. | `submit` |

The manager MUST receive every message with room for both kinds and
for the number of descriptors in §7.A. It MUST detect ancillary data
the kernel could not fit (`MSG_CTRUNC`) and MUST answer the message
`INVALID_ARGUMENTS` without acting on it: a request whose attachments
were partly lost does not describe the job the submitter meant.

Attachments on a message whose command does not use them MUST be
closed and ignored. A stray descriptor on a `status` is not an error,
in the same spirit as §4.8's rule for fields that do not apply — but
it is closed, because nothing else could own it.

The manager MUST close every attached descriptor it does not hand to a
job or adopt as an output sink, on every path including error paths.
A submitter MUST assume the manager has taken ownership of everything
it attached to a `submit`, whatever the outcome, and MUST NOT rely on
the manager leaving a descriptor open.

A response MAY carry ancillary data. One kind is defined:

| Level | Type | Meaning | Carried by |
|---|---|---|---|
| `SOL_SOCKET` | `SCM_RIGHTS` | The job's process handle. Exactly one. | A `submit` response for a running job. §7.6 |

A submitter that receives a response without room for its ancillary
data does not receive the handle, and MUST NOT treat that as an error:
the response content is complete without it.

## Requests

A request is one JSON object.

```json
{"command": "submit", "image_path": "/usr/bin/peios-backup",
 "arguments": ["sync", "/home/u/docs"], "description": "Backup of docs"}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `command` | string | always | `submit`, `status`, `wait`, `stop` or `signal`. |
| `job_id` | string | all but `submit` | The job. |
| `wait` | bool | no | For `stop`: block until the job is terminal. §7.8 |
| `for` | string | no | For `wait`: `ready` or `terminal`. §7.8 |
| `signal` | integer | for `signal` | The signal number. §7.8 |

The `submit` definition fields are in §7.6.

`command` MUST be present and MUST be a string naming one of the five
commands. Otherwise the manager MUST answer `INVALID_COMMAND`.

`job_id` MUST be present and a string for every command but `submit`.
Its absence, a non-string value, or a value that is not a well-formed
identifier MUST be answered `INVALID_ARGUMENTS`.

A field the command does not use MUST be ignored, not rejected. A
field the manager does not recognise MUST be ignored (§7.11).

## Responses

Every response carries a `status` field, exactly `"ok"` or `"error"`.

The success shape for every command is the **job view** (§7.7):

```json
{"status": "ok", "job": { … }}
```

The error shape is §4.9's:

```json
{"status": "error", "code": "QUOTA_EXCEEDED",
 "message": "submitter S-1-5-21-… holds 64 live jobs"}
```

`code` MUST be one of the values in §7.10. `message` is not
normative; a submitter MUST NOT parse or branch on it.

## Closing after an error

§4.5's distinction applies. On a sequenced-packet socket a
frame-level failure is narrower — the transport cannot lose
synchronisation — so only `REQUEST_TOO_LARGE` and a truncated message
close the connection. Every other error is command-level: the manager
MUST send the error and keep the connection open.

A submitter MUST NOT assume a connection survives an error response.
