---
title: Responses
description: The four response kinds a query can receive, how records are chunked, and how errors and timeouts are reported.
---

A response is a MessagePack map whose `status` field names its kind.
There are four.

| `status` | Carries | Meaning |
|---|---|---|
| `"ok"` | `records` | A chunk of result records. |
| `"end"` | — | The non-streaming query is complete. |
| `"watch"` | — | The streaming query's initial result set is complete. |
| `"error"` | `error` | The query failed. |

## Result messages

An `"ok"` message carries `records`, an array of flat maps (§3.22).

Records are chunked at record boundaries: a successful query sends one
or more `"ok"` messages, each within the message ceiling (§3.15). A
collector MUST NOT split one record across two messages. A record too
large to fit in a message alone MUST fail the query with an error rather
than being truncated, partially sent, or skipped.

Each record is self-describing and records in one response MAY carry
different sets of keys — event payload fields vary by event type, metric
labels vary by series. A client MUST NOT assume a uniform schema across
a result set, and MUST NOT infer that a key absent from one record is
absent from the data.

A successful query with no matching records sends exactly one `"ok"`
message with an empty `records` array, then its terminal message. A
collector MUST NOT omit it: "no records" and "the query has not yet
produced records" are different states and a client must be able to tell
them apart.

## The two terminal messages

`"end"` terminates a non-streaming query. `"watch"` marks the point in a
streaming query where the stored result set ends and live delivery
begins (§3.27). A query sends exactly one of them, never both.

Until one has arrived, **the query has not succeeded**. A collector that
fails partway through MUST send `"error"`, and a client that receives
`"error"` before either terminal message MUST discard every `"ok"`
message it received for that query. Partial results are not results:
they are an arbitrary prefix of an ordering that was never completed,
and a client that kept them would silently under-report.

An `"error"` *after* `"watch"` is different. It terminates the stream,
and the records already delivered remain valid — they were complete when
they were sent, and the ordering they belonged to had already closed.

## Errors

An `"error"` message carries `error`, a human-readable string.

There is no error code and no machine-readable classification. This is a
deliberate limit on the interface: an error here is a parse failure, a
type mismatch, a timeout, a limit, or a refusal, and a client's response
to all of them is the same — show it to whoever wrote the query. A
client MUST NOT parse the string, and a collector MAY change the wording
of any error at any time.

A collector MUST NOT include in an error message any value the client
was not authorized to read (§3.28).

## Timeouts

A collector MUST bound the time a query may take to reach its terminal
message.

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

The clock starts once the request has been decoded and the caller's
token obtained, and it covers everything that follows: parsing, access
checks, cross-type pre-computation, execution, merging, aggregation,
pagination, projection and transmission. A collector MUST send `"end"`,
or for a streaming query `"watch"`, before it expires.

The timeout bounds the **initial result set only**. Once a streaming
query has sent `"watch"` its watch phase is not time-limited; what
bounds it instead is the streaming concurrency limit (§3.14), the
distinct-value limit (§3.27), and the client's own ability to keep up
(§3.27).

On expiry a collector MUST cancel the query and send `"error"`. Any
`"ok"` messages already sent are discarded by the client under the rule
above.
