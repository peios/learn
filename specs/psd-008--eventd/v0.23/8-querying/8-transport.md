---
title: Transport
---

## Socket interface

eventd MUST expose a Unix domain socket for query access. The socket path is configured via the `QuerySocketPath` registry key under `Machine\System\eventd\`. There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

The query socket is shared across all three data types. The query mode (EVENTS, LOGS, METRIC) is determined by parsing the query string, not by the transport.

## Wire protocol

The query protocol is request-response over the Unix socket. Each message is a length-prefixed msgpack-encoded value:

| Field | Type | Size | Description |
|---|---|---|---|
| `length` | `u32` | 4 bytes | Total length of the msgpack payload in bytes. Little-endian. |
| `payload` | msgpack | `length` bytes | The request or response body. |

eventd MUST reject messages whose `length` exceeds `MaxQueryMessageBytes`. This prevents a malicious or buggy client from forcing a large memory allocation before the query is even parsed.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxQueryMessageBytes | REG_DWORD | 65536 | 1024--16777216 | Maximum permitted query message size in bytes. Messages exceeding this limit are rejected without reading the payload. |

### Request format

A query request is a msgpack map:

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | The query string. |

### Response format

**Result message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"ok"`. |
| `records` | array of map | Result records. Each record is a flat msgpack map. |

Each record is a self-describing map. Different records in the same response MAY have different sets of keys (event payload fields vary by event type, metric labels vary by series).

**End message:**

| Field | Type | Description |
|---|---|---|
| `status` | string | `"end"`. |

Sent after the last result message for non-streaming queries.

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
| String | msgpack string |
| GUID | msgpack string in standard GUID format |
| Boolean | msgpack boolean |
| Nested map (payload) | msgpack map |
| Array (payload) | msgpack array |
| NULL | msgpack nil |

### Streaming responses

For streaming queries, eventd sends the initial result set, then continues sending result messages as new matching records are committed. There is no end message for streaming queries.

## Connection lifecycle

One query per connection. Multiple concurrent queries require multiple connections. The connection is closed after the end message (non-streaming) or on client disconnect (streaming).

## Access control

Query access control is defined in the access control chapter. eventd checks the connecting process's credentials before executing the query.
