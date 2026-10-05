---
title: The Native Channel
description: The Unix socket, the observability query framing it reuses, one request per connection, and the control object every request is checked against.
---

The native door is a `SOCK_STREAM` Unix socket at a configured path —
`/run/resolvd/resolv.sock` on Peios. [*nri-native.stream-socket-at-configured-path] Every process MAY connect; what a
connection may ask is decided by the control object, not by reaching the
socket. [*nri-native.every-process-may-connect]

## Framing

Messages in both directions are length-prefixed MessagePack values in
the observability query framing (§3.15): [*nri-native.length-prefixed-messagepack-framing]

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `length` | Length of the payload in bytes, little-endian [*nri-native.length-is-little-endian] |
| 4 | `length` | `payload` | A MessagePack map |

A request is a map with a required `query` string naming the request
(§6.5). [*nri-native.request-carries-query-string] A reply is a map with a required `ok` boolean; when `ok` is
`false` it carries `error`, a string for a person, and nothing else. [*nri-native.error-reply-carries-only-error]
When `ok` is `true` it carries `kind` — `answer`, `addresses`, `status`
— or nothing, for a request with no body to return. [*nri-native.success-reply-carries-kind]

A receiver MUST ignore keys it does not know [*nri-native.unknown-keys-ignored] and MUST reject a message
that repeats a key. [*nri-native.duplicate-keys-rejected] A resolver MUST refuse a request whose `length`
exceeds the message ceiling (§6.A2) without reading the payload, [*nri-native.oversized-request-refused-unread] and
MUST reply with an error rather than closing silently. [*nri-native.oversized-request-answered-with-error]

## One request per connection

A connection carries exactly one request and one reply. [*nri-native.one-request-per-connection] The client
sends, the resolver answers, and either side closes. There is no
pipelining and no conversation identifier: the shim that generates most
of the traffic is loaded into processes that fork, and a connection
held across a fork is how a resolver hands back somebody else's answer.
Connecting to a Unix socket is cheap; the cache that would make it
cheaper lives in the resolver, where every caller shares it.

A resolver MUST bound how long a connection may take to deliver its
request, and MUST drop one that exceeds the bound. [*nri-native.request-delivery-bounded] A client with a
half-sent request holds a few bytes of buffer, never the resolver.

## The control object

Every request names a right (§6.5). Before acting, a resolver MUST
perform an access check of that right against its **control object**
using the token of the connecting peer — the peer's real token, as the
kernel would judge it, never a numeric credential read from the socket. [*nri-native.access-check-with-peer-token]

The control object's descriptor is `Machine\System\Network\Dns
ControlSecurity` when that value holds a valid self-relative descriptor,
else the resolver's compiled default. [*nri-native.control-descriptor-from-registry-else-default] The default MUST grant
`RESOLVER_QUERY` to Everyone and `RESOLVER_ALL_ACCESS` to SYSTEM and
Administrators. [*nri-native.default-descriptor-grants]

| Right | Value | Governs |
|---|---|---|
| `RESOLVER_QUERY` | `0x0001` | `resolve`, `lookup`, `reverse`, `status` [*nri-native.resolver-query-right] |
| `RESOLVER_CONTROL` | `0x0002` | `flush` [*nri-native.resolver-control-right] |
| `RESOLVER_ALL_ACCESS` | `0x000F0003` | Both, with the standard rights [*nri-native.resolver-all-access] |

A denied request is answered with an error reply, not a closed
connection. [*nri-native.denied-request-answered-with-error]

The peer's identity is what identity-aware resolution policy will key
on. This version defines no such policy; a resolver MUST NOT invent one. [*nri-native.no-identity-aware-policy]
