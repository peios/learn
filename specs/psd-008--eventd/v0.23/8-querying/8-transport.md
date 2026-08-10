---
title: Transport
---

## Socket interface

eventd MUST expose an `AF_UNIX` `SOCK_STREAM` socket for query access. The
socket path is configured via the `QuerySocketPath` registry key under
`Machine\System\eventd\`. There is no compiled-in default -- if the key does not
exist or is invalid, eventd MUST fail to start.

The query socket is shared across all three data types. The query mode (EVENTS, LOGS, METRIC) is determined by parsing the query string, not by the transport.

After binding the query socket, eventd MUST set its filesystem mode to `0666`
before listening and MUST NOT rely on process umask for the final permissions.
Read access is enforced by KACS on each connection; the socket pathname mode is
only the coarse gate that allows local clients to reach eventd. Administrators
who need a narrower coarse gate must place the socket inside a directory with
restrictive permissions.

## Wire protocol

The query protocol is request-response over the Unix socket. Each message is a length-prefixed msgpack-encoded value:

| Field | Type | Size | Description |
|---|---|---|---|
| `length` | `u32` | 4 bytes | Total length of the msgpack payload in bytes. Little-endian. |
| `payload` | msgpack | `length` bytes | The request or response body. |

eventd MUST reject inbound messages whose `length` exceeds
`MaxQueryMessageBytes` by closing the connection without reading the payload.
This prevents a malicious or buggy client from forcing a large memory
allocation before the query is even parsed. eventd MUST also ensure every
outbound response payload is no larger than `MaxQueryMessageBytes`.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxQueryMessageBytes | REG_DWORD | 65536 | 1024--16777216 | Maximum permitted query request or response msgpack payload size in bytes. Inbound messages exceeding this limit are rejected without reading the payload. |

### Request format

A query request is a msgpack map:

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | The query string. |

If the request payload is not valid msgpack, is not a map, omits `query`,
contains a non-string `query`, or contains duplicate top-level keys, eventd MUST
send an error response and close the connection. Unknown request fields MUST be
ignored when they are not duplicates of another request key.

### Response format

**Result message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"ok"`. |
| `records` | array of map | Result records. Each record is a flat msgpack map. |

Each record is a self-describing map. Different records in the same response MAY have different sets of keys (event payload fields vary by event type, metric labels vary by series).

Result messages are chunked at record boundaries. A successful query sends one
or more result messages, each with a `records` array whose encoded response
payload is no larger than `MaxQueryMessageBytes`. If a successful query has no
records, eventd sends exactly one result message with `records = []`. eventd
MUST NOT split a single record across messages. If one encoded result record is
too large to fit in a response message, the query MUST fail with an error
instead of sending a truncated or partial record.

**End message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"end"`. |

Sent after the last result message for non-streaming queries. A non-streaming
successful query is complete only after the end message has been sent. If an
error message is sent before `end`, the query failed and any earlier result
messages for that query MUST be discarded by the client.

**Watch message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"watch"`. |

Sent exactly once for streaming queries, after the initial result messages and
before the streaming watch phase begins. A streaming query is established only
after the watch message has been sent. If an error message is sent before
`watch`, the query failed and any earlier initial result messages for that query
MUST be discarded by the client. If an error message is sent after `watch`, the
stream is terminated and earlier records remain valid.

**Error message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"error"`. |
| `error` | string | Error description (parse error, timeout, type mismatch, etc.). |

### Value encoding

| Value type | Msgpack encoding |
|---|---|
| Integer | msgpack integer |
| Float | msgpack float64 |
| Timestamp | msgpack integer, nanoseconds since Unix epoch (§1.3) |
| String | msgpack string |
| GUID | msgpack string in PSD-002 canonical GUID form (lowercase, braced) |
| Binary | msgpack bin |
| Boolean | msgpack boolean |
| Array (payload) | msgpack array |
| NULL | msgpack nil |

Event payload maps are flattened before they are emitted in result records, as
defined in §8.1. A msgpack map in the stored payload is therefore a container for
flattening and is not emitted as a nested map value in an event result record.
Msgpack arrays remain array values; maps nested inside arrays are preserved as
array contents and are not traversed for query-language fields. Msgpack `bin`
payload values remain binary values and are emitted as msgpack bin.

### Streaming responses

For streaming queries, eventd sends the initial result set using the same
result-message chunking rules as non-streaming queries, sends a `watch` message,
then continues sending result messages as new matching records are committed.
There is no end message for streaming queries. If a streamed result record is too
large to fit in one response message, eventd MUST terminate the streaming query
with an error.

## Connection lifecycle

One query per connection. Multiple concurrent queries require multiple connections. The connection is closed after the end message (non-streaming) or on client disconnect (streaming).

## Access control

Query access control is defined in the access control chapter. eventd checks the connecting process's credentials before executing the query.
