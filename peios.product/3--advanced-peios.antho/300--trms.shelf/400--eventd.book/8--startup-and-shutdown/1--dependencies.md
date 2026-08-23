---
title: Dependencies
description: The four subsystems eventd needs before it can do anything, the one that is not really a dependency, and where it sits in the boot.
---

eventd needs four subsystems before it can do anything.

| Subsystem | For |
|---|---|
| KMES | Event ingestion. Available as soon as PKM is loaded. |
| LCS and loregd | Configuration. eventd reads every setting from the registry. |
| KACS | Access control — the AccessCheck API for query authorization, and `kacs_open_peer_token` for caller identification. |
| peinit | The boot ID, and lifecycle management. |

eventd is a peinit-managed service, started after loregd is available —
it cannot read a single configuration value without the registry, and it
has no compiled-in defaults for the six paths it needs (§A).

## The dependency that is not one

KACS is needed to *serve* queries and not to ingest. The drain, write
and retention paths never call it. That asymmetry is what lets eventd
keep ingesting through a KACS outage while refusing every query (§9.3),
and it is the right way round: losing the ability to read the audit
store is recoverable, losing the events is not.

## Ordering in the boot

eventd is one of the platform daemons and is Critical: peinit reboots
the system rather than continuing without it. It comes up after loregd
and authd, and it stops before them on the way down — it is among the
last services shut down, because everything else's shutdown is worth
recording.

The window before eventd exists is real and peinit covers it by
buffering service output until the log socket appears. Events emitted
during that window are not lost either: they sit in the KMES ring
buffers, and eventd's first drain after attaching reads them from
`tail_pos` (§2.2).
