---
title: Terminology
---

Terms defined in PSD-003 (KMES, event, header, payload, stamp, ring buffer, boot buffer, consumer, origin class, event type, sequence number) are used here with the same meaning and are not redefined.

Terms defined in PSD-004 (token, GUID, SID, Security Descriptor, ACL, ACE, privilege, SeAuditPrivilege, SeSecurityPrivilege) are used here with the same meaning and are not redefined.

Terms defined in PSD-005 (registry, hive, key, value, layer) are used here with the same meaning and are not redefined.

The following terms are specific to this specification.

**eventd**: The Peios observability daemon. A userspace process managed by peinit that consumes events from KMES, ingests logs and metrics from service processes, and provides persistent storage and querying for all three data types.

**Event store**: The persistent storage engine for KMES events. Receives structured event records with full header metadata (timestamps, sequence numbers, identity GUIDs) and makes them queryable.

**Log store**: The persistent storage engine for log records. Receives log entries from service processes and makes them queryable.

**Metric store**: The persistent storage engine for metric data. Receives numeric time-series measurements and makes them queryable.

**Log record**: A single log entry as stored by eventd. Contains the log message, a severity level, a timestamp, and metadata identifying the emitting service.

**Boot ID**: A GUID assigned by peinit at each boot, used by eventd to partition data across boots. Events, logs, and metrics from different boots are never interleaved in storage.

**Retention policy**: A set of rules governing how long stored data is kept before deletion. Retention policies are configured per data type via the registry and enforced by eventd.
