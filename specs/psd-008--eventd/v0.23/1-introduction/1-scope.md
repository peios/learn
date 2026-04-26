---
title: Scope
---

This specification defines eventd, the observability daemon for the Peios operating system. eventd is one of the five Peios system daemons managed by peinit. It is the sole persistent sink for observability data in Peios -- all events, logs, and metrics flow through eventd for storage, indexing, and querying.

eventd handles three distinct data types, each with its own ingestion path, storage engine, and query semantics:

- **Events** -- structured records emitted through KMES (Kernel Mediated Event Subsystem). eventd consumes events from KMES per-CPU ring buffers and persists them with full header metadata including identity stamps. Events are the primary audit and security telemetry.
- **Logs** -- unstructured or semi-structured text output from services and system components. eventd ingests logs through a dedicated mechanism independent of KMES.
- **Metrics** -- numeric time-series data representing system and service measurements. eventd ingests metrics through a dedicated mechanism independent of KMES.

This specification covers:

- The event ingestion pipeline -- KMES ring buffer consumption, event processing, and persistence
- The log ingestion pipeline -- transport mechanism, log record format, and persistence
- The metric ingestion pipeline -- transport mechanism, metric data model, and persistence
- Storage -- the storage engine for each data type, retention policies, and lifecycle management
- Querying -- the interface through which other daemons and tools retrieve stored observability data
- Access control -- Security Descriptor-based authorization for reading and writing observability data
- Configuration -- registry-based operational parameters
- Startup and shutdown -- bootstrap sequence, crash recovery, and graceful termination
- Failure modes -- behavior under resource exhaustion, KMES overrun, storage failure, and daemon restart

This specification does not cover:

- KMES (covered by PSD-003)
- Event type schemas or naming conventions for kernel-emitted events (defined by the emitting subsystem's specification: PSD-004 for KACS events, PSD-005 for LCS events)
- KACS (covered by PSD-004)
- LCS (covered by PSD-005)
- peinit service management (covered by PSD-007)
- Authentication or principal management (authd)
- Log collection from remote hosts (future scope)
- Metric collection or scraping from external sources (future scope)
