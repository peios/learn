---
title: Compatibility
---

KMES is not a port or reimplementation of any existing event subsystem. The design -- structured events with a fixed binary header and msgpack payload, a shared memory ring buffer for delivery, and a single emission path for both kernel and userspace -- was chosen to meet the specific requirements of Peios: unified observability, trusted kernel-stamped metadata, and a simple delivery mechanism.

KMES serves a similar role to ETW (Event Tracing for Windows) in the Windows kernel and the audit subsystem (auditd) in Linux. It is not compatible with either at the wire level, format level, or API level.

## Features handled by other subsystems

| Feature | Subsystem |
|---|---|
| Event persistence and querying | eventd |
| Event type schemas and naming conventions | eventd |
| Boot identity and cross-boot sequencing | peinit / eventd |
