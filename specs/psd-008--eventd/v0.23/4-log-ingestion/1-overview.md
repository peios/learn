---
title: Overview
---

Logs are fundamentally text. A log entry is a line of text output by a service or system component, with light metadata attached by the ingestion layer. eventd does not parse or interpret log text -- if the text happens to be JSON or structured in some other way, that is the service's concern, not eventd's.

Structured observability data belongs in events (via KMES), not logs. The boundary is clear: events are typed, schema'd, kernel-stamped records with identity. Logs are human-readable text output. The "peiosification" of Linux software includes a translation layer that converts relevant log output into proper events where structured data is needed.

## Loss tolerance

Log loss is tolerable. Unlike events, where a lost record may represent a missed security audit entry, a lost log line is an inconvenience, not a failure. This tolerance shapes the entire log ingestion design:

- The ingestion path does not track sequence numbers or detect gaps.
- If the transport buffer fills, log records are dropped without notification.
- No synthetic gap records are generated for lost logs.
- eventd MAY maintain a dropped-log counter for observability, but this is not a normative requirement.

## Ingestion path

Logs are ingested over a Unix domain socket. The socket accepts connections from any process with the appropriate credentials. The primary log producer is peinit, which captures stdout and stderr from the services it manages and forwards them to eventd. Native Peios services MAY also write directly to the log socket.

peinit is not a privileged log source -- it uses the same socket and protocol as any other log producer. Its role is to bridge the gap between services that write to stdout/stderr (the standard Unix model) and eventd's log ingestion interface.
