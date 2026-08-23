---
title: Prior Art
description: Where eventd sits against Windows Event Log, ETW, journald, Prometheus and OpenTelemetry, and what it deliberately leaves to others.
---

eventd is not a port of anything. It occupies a position several
existing systems also occupy, and differs from each of them in ways
worth being explicit about. PSPU §3.C compares the wire contracts; this
compares the systems.

## Windows Event Log and ETW

The closest structural match. Windows splits the job in two: Event
Tracing for Windows delivers events from kernel and application
providers, and the Event Log service persists and serves them. Peios
splits it the same way, with KMES in the ETW position and eventd in the
Event Log service's.

Held in common: kernel-mediated delivery with metadata the emitter
cannot forge, a userspace service owning persistence, and access control
by Security Descriptor on a named channel — which in eventd becomes a
descriptor per event type pattern (§7.2).

Different: eventd unifies three data types where Windows separates them
across the Event Log, ETL trace files and Performance Counters. eventd
stores in SQLite rather than a proprietary binary format. And ETW's
buffering is a kernel-managed trace session, where KMES exposes
shared-memory ring buffers with a lock-free consumer protocol that
eventd drains directly (§2.2).

## journald

journald is the systemd system journal: it captures service output and
structured messages and stores them in an indexed binary journal.

Held in common: a single daemon for system-wide log ingestion, capturing
standard output and standard error as records with metadata attached,
stored in a binary format with indexes.

Different: journald is log-only, and a systemd system needs a separate
stack for metrics. journald's access control is Unix file permissions
and polkit, where eventd's is KACS Security Descriptors evaluated per
record and per field (§7). And journald reads kernel messages from
`/dev/kmsg`, a text interface with no identity, where eventd receives
kernel events through KMES with the kernel's own identity stamps intact.

The similarity worth noting is that journald's storage is also its
index, and its query surface is a matcher over fields rather than a
language. eventd goes further in that direction — an actual query
language, over all three data types — for the reason PSPU §3.C gives:
computing on the collector's side is what lets access control constrain
the computation.

## Prometheus and OpenTelemetry

Prometheus is a pull-based metrics system with a local time-series
database; OpenTelemetry is a vendor-neutral collection framework
spanning traces, metrics and logs.

eventd's metric store fills roughly the role of a local Prometheus TSDB,
and takes the Prometheus data model — a name plus labels identifying a
series, cumulative-bucket histograms — more or less wholesale (§5.2).

Different: eventd is pushed to rather than scraping. It implements no
distributed tracing at all. And where OpenTelemetry's answer to the
three-signal problem is a common collection framework in front of three
backends, eventd's is one backend with one access control model and one
query surface — which is the whole design bet.

## Deliberately elsewhere

| Concern | Where it lives |
|---|---|
| Event emission, buffering and delivery | KMES, in the Peios Kernel TRM; the consumer protocol in PSPK |
| Event type vocabulary and payload schemas | the emitting subsystem's own documentation |
| Access control primitives | KACS, in the Peios Kernel TRM |
| Configuration storage | LCS and loregd |
| Daemon lifecycle, and forwarding service output | peinit |
| The three interfaces eventd exposes | PSPU §3 |
