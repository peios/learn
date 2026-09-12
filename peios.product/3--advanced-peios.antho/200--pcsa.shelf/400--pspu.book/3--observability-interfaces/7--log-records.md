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
It also matches every origin whose part before a slash is `svc`, such as
`svc/HealthCheck`, because matching considers only that part.

A producer therefore SHOULD choose an origin that names it stably and
distinguishably, and SHOULD use dots for hierarchy, because an
administrator writing an access rule has nothing else to write it
against.

An origin MUST match:

```text
origin    := component | component "/" producer
producer  := component | component "[" [0-9]+ "]"
component := [A-Za-z0-9_][A-Za-z0-9_.-]*
```

A collector MUST discard a record whose origin does not.

A single component is the identifier grammar of §3.19, widened only to
admit a leading digit, and names a program. The optional second
component names a **producer within** that program — a hook, a reload
command, a health check, one submitted job — and the bracketed integer
distinguishes several of the same kind. A forwarding service manager
uses it for exactly that: `jellyfin/ExecStartPre[0]` is a pre-start
hook's output, `jellyfin/HealthCheck` a health check's, `jobs/<guid>` a
submitted job's. There is at most one slash, and the index may appear
only after one.

Everything the grammar still excludes, it excludes on purpose. An
origin is not merely a label: it is matched against patterns in which
`*` is the wildcard, so an origin containing `*` could not be selected
exactly and could match a rule its producer was never meant to satisfy;
and it is the name an access rule is stored under, so an origin carrying
a backslash, a quoting character or whitespace could land somewhere
other than where the administrator who wrote the rule believes it is.
Constraining the producer is the only point at which either can be
prevented.

The slash is safe there only because it is never written into a stored
rule. A collector MUST resolve the access rule for an origin from the
part **before** the slash, so that a service's hooks, reloads, health
checks and jobs answer to the rule written against the service — and a
producer cannot reach a rule of its own by inventing a second component.

A collector MUST count discarded origins and MUST make that count
observable to an operator. An unrecognised origin means a producer's
vocabulary and a collector's have drifted apart, and every line that
producer sends is being dropped; a silent discard makes the most
complete kind of log loss the least visible one.

Quoted forms remain valid syntax everywhere an origin may be written
(§3.24). A single-component origin beginning with a letter or `_` never
needs them; every other conforming origin does, because the query
language's identifiers admit neither a slash, a bracket nor a leading
digit (§3.19). A *pattern* may need them too, and a collector holding
origins stored before this rule applied must still be able to return and
select them.

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
