---
title: Transport
---

## Log socket

eventd MUST expose a Unix domain datagram socket for log ingestion. The socket path is configured via the `LogSocketPath` registry key under `Machine\System\eventd\`. There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

Datagram sockets are used rather than stream sockets because each log record is an independent message with no framing concerns. A datagram either arrives completely or not at all -- no partial reads, no length-prefix parsing, no connection state.

## Log record format

Each datagram is a single msgpack-encoded map representing one log record:

| Field | Type | Required | Description |
|---|---|---|---|
| `origin` | string | Yes | Name of the service or component that produced the log line. For peinit-forwarded logs, this is the service name. For direct logging, this is the identity of the sending process. |
| `is_error` | bool | Yes | True if the log line was captured from stderr or explicitly marked as error by the sender. False for stdout / normal output. |
| `message` | string | Yes | The log text. A single line of output. |
| `timestamp` | u64 | No | Wall clock timestamp in nanoseconds since Unix epoch, as captured by the sender. If omitted, eventd uses its own wall clock at receipt time. |

peinit SHOULD include the timestamp captured at the time the line was read from the service's pipe, not the time it was forwarded to eventd. This preserves timing accuracy when peinit batches log records.

## Malformed input handling

If a datagram contains invalid msgpack (not decodable), the entire datagram MUST be dropped silently.

If a datagram contains a valid msgpack value that is not a map and not an array of maps, it MUST be dropped silently.

For a single record (map), if a required field is missing or has the wrong type (e.g., `origin` is an integer instead of a string), the record MUST be dropped silently.

For a batched datagram (array of maps), each record is validated independently. Invalid records MUST be dropped. Valid records in the same batch MUST still be processed. One malformed record MUST NOT cause the entire batch to be discarded.

eventd MUST NOT emit synthetic events, log errors, or increment visible counters in response to malformed input. These are untrusted inputs from arbitrary senders -- reacting to invalid data would be a denial-of-service vector.

> [!INFORMATIVE]
> The `is_error` field is deliberately a boolean, not a severity level. peinit can distinguish stdout from stderr and nothing more. Richer severity (debug, info, warn, error, fatal) is a log-framework concern -- services that encode severity in their output can do so textually. Services that need structured severity levels should emit events, not logs.

## Batching

Senders MAY batch multiple log records into a single datagram by sending a msgpack array of log record maps instead of a single map. eventd MUST accept both forms -- a single map (one record) or an array of maps (multiple records).

Batching amortises syscall overhead. peinit SHOULD batch log records when forwarding under sustained load. The batch size is bounded by the maximum datagram size supported by the Unix socket (implementation-defined, typically 212992 bytes on Linux).

## Dropped records

If the socket receive buffer is full when a sender transmits a datagram, the kernel drops the datagram silently (standard Unix datagram socket behavior). Neither the sender nor eventd is notified.

eventd SHOULD NOT increase the socket receive buffer beyond a reasonable size. If eventd cannot drain the socket fast enough, logs are dropped. This is by design -- log ingestion MUST NOT exert backpressure on senders. A service MUST NOT stall because eventd is slow.

> [!INFORMATIVE]
> The default Linux `SO_RCVBUF` for Unix datagram sockets is approximately 212 KB, which holds roughly 1000 typical log records. During a batch commit (1-10ms), this buffer is the only cushion. Under burst conditions (e.g., a service dumping a stack trace), some datagrams will be dropped. This is the intended degradation mode for a loss-tolerant data path -- the alternative (backpressure or unbounded buffering) would violate the design constraint that log ingestion must never slow senders.

## Direct service logging

A native Peios service that wants to log directly to eventd (bypassing peinit) uses the same socket and the same record format. The service sets the `origin` field to its own service name. No additional setup or negotiation is required.

Direct logging is a convenience for services that want more control over log metadata than stdout/stderr provides. It is not required -- most services log via stdout/stderr and peinit handles the rest.
