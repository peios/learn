---
title: Prior Art
---

eventd is not a port or reimplementation of any single existing system. Its design draws on several established approaches while making different trade-offs.

## Windows Event Log / ETW

Windows provides Event Tracing for Windows (ETW) for kernel and application event delivery, and the Windows Event Log service for persistence and querying. KMES (PSD-003) fills the ETW role; eventd fills the Event Log service role. Key similarities:

- Kernel-mediated event delivery with trusted metadata (ETW providers / KMES emitters)
- A userspace service responsible for persistence (Event Log service / eventd)
- Channel-based access control using Security Descriptors (Windows Event Log channels / eventd event access control)

Key differences:

- eventd unifies events, logs, and metrics in a single daemon. Windows separates these across Event Log, ETL trace files, and Performance Counters.
- eventd uses SQLite for persistent storage. Windows Event Log uses a proprietary binary format (EVTX).
- KMES uses shared memory ring buffers with lock-free protocols. ETW uses kernel-managed trace sessions with different buffering semantics.

## journald (systemd)

journald is the system journal daemon in systemd-based Linux distributions. It captures structured log messages from services (via stdout/stderr and the journal socket) and stores them in a binary journal format.

Key similarities:

- Captures service stdout/stderr as structured log records with metadata
- Single daemon for system-wide log ingestion
- Binary storage format with indexing

Key differences:

- eventd handles events and metrics in addition to logs. journald is log-only (metrics require a separate stack like Prometheus/node_exporter).
- eventd enforces access control via KACS Security Descriptors. journald uses Unix file permissions and polkit.
- eventd receives kernel events through KMES ring buffers. journald receives kernel messages through /dev/kmsg.

## Prometheus / OpenTelemetry

Prometheus is a pull-based metrics system. OpenTelemetry defines a vendor-neutral telemetry collection framework spanning traces, metrics, and logs.

eventd's metric store serves a similar role to a local Prometheus TSDB, but:

- eventd is push-based (services push metrics to eventd), not pull-based (Prometheus scrapes endpoints).
- eventd does not implement distributed tracing. Traces are out of scope.
- eventd integrates metrics with events and logs under a single access control model and query interface, rather than requiring separate systems.

## Features handled by other subsystems

| Feature | Subsystem |
|---|---|
| Event emission, buffering, and delivery | KMES (PSD-003) |
| Event type schemas for KACS events | KACS (PSD-004) |
| Event type schemas for LCS events | LCS (PSD-005) |
| Daemon lifecycle management | peinit (PSD-007) |
| Access control primitives (tokens, SDs, access checks) | KACS (PSD-004) |
| Registry storage and configuration | LCS (PSD-005) / loregd (PSD-006) |
