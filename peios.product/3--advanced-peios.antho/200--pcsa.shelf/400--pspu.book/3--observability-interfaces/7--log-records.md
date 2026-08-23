---
title: Log Records
description: The MessagePack map that carries a log record, one or batched — origin, is_error, timestamp and job_id.
---

A log datagram carries either **one** record, encoded as a MessagePack
map, or **several**, encoded as a MessagePack array of maps. A collector
MUST accept both forms. A producer MAY use either at any time; there is
no mode and no negotiation.

## Fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `origin` | string | yes | Non-empty name of the program that produced the line. |
| `is_error` | bool | yes | True if the line came from standard error, or the producer marked it an error. False otherwise. |
| `message` | string | yes | The log text — one line of output. MAY be empty, which is a blank line. |
| `timestamp` | integer | no | When the line was produced, in the timestamp domain (§3.5). Absent means the collector uses its own clock at receipt. |
| `job_id` | binary, 16 bytes | no | A GUID in PCDS binary layout correlating this line to one execution of one program. |

A collector MUST ignore fields it does not recognise (§3.29).

## `origin`

`origin` is what the producer says it is. A collector MUST NOT verify
it, because it has no way to: the channel is a datagram socket and
carries no peer identity (§3.4). Two producers MAY use the same origin,
and one producer MAY use several.

An origin is nonetheless the unit that read access is granted on
(§3.28), and a collector matches it against patterns using dot-delimited
prefix semantics: the pattern `svc` matches the origin `svc` and any
origin beginning `svc.`, and matches neither `svc_daemon` nor `svcfoo`.

A producer therefore SHOULD choose an origin that names it stably and
distinguishably, and SHOULD use dots for hierarchy, because an
administrator writing an access rule has nothing else to write it
against.

An origin MUST match the identifier grammar of §3.19:

```text
[A-Za-z_][A-Za-z0-9_.-]*
```

A collector MUST discard a record whose origin does not.

The constraint exists because an origin is not merely a label. It is
matched against patterns in which `*` is the wildcard, so an origin
containing `*` could not be selected exactly and could match a rule its
producer was never meant to satisfy; and it is the name an access rule
is stored under, so an origin carrying a path separator or a quoting
character could land somewhere other than where the administrator who
wrote the rule believes it is. Constraining the producer is the only
point at which either can be prevented.

Quoted forms remain valid syntax everywhere an origin may be written
(§3.24). A conforming origin never needs them, but a *pattern* may, and
a collector holding origins stored before this rule applied must still
be able to return and select them.

## `is_error`

`is_error` is a boolean and deliberately not a severity level.

A forwarding producer can distinguish standard output from standard
error and nothing more; inventing five levels out of two file
descriptors would be a guess presented as data. A producer with real
severity levels either writes them into the message text, where they are
text and are searched as text, or emits events, which have types.

## `timestamp`

A producer SHOULD supply the timestamp it captured when the line was
produced, not when it submitted it. A producer that batches (§3.8) and
omits the field attributes every line in the batch to the moment the
collector happened to read it, which discards the timing information the
batch was accumulated over.

## `job_id`

`job_id` correlates a line to a single execution rather than to a
program. A forwarding producer sets it so that the output of one run of
a service can be separated from the run before and the run after; a
producer with no such notion omits it.

A collector MUST treat it as an opaque 16-byte value. Nothing in this
chapter interprets it, and a producer MAY use it for any correlation of
its own, provided the value is a GUID.
