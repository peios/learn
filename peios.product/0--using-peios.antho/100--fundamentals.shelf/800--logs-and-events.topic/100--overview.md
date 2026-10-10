---
title: What the machine records
type: concept
description: eventd keeps three records of what happens on a Peios machine — logs, events and metrics — and shows each person only what they may read.
related:
  - peios/logs-and-events/event-viewer
  - peios/logs-and-events/find-missing-records
  - peios/logs-and-events/save-incident-evidence
  - peios/services-and-jobs/output-and-logging
  - peios/auditing/overview
---

Start with [Event Viewer](~peios/logs-and-events/event-viewer) to inspect a
machine's logs, events and metrics. **eventd** receives these records,
stores them and answers queries about the stored history you may read.
If the records you expect are missing, follow
[Find missing records](~peios/logs-and-events/find-missing-records) before
changing settings or removing stored data.

## Three kinds of record

eventd keeps three kinds of record, which arrive by different routes and
answer different questions.

| Kind | What it is | Where it comes from |
|---|---|---|
| **Logs** | Lines of text that services and jobs write | The service manager, peinit, which captures stdout and stderr except for services attached to a terminal with `TTYPath` |
| **Events** | Structured records of something that happened, such as a service started or an access refused | The kernel and system programs |
| **Metrics** | Numbers measured over time, such as how many requests a server has answered | Programs that publish them |

### Logs

A log line is what a program wrote to its **standard output** or **standard
error**, the two streams every program writes text to. Each line carries:

- **where it came from**, its *origin*: the service's name, such as `sshd`.
  Output from a service's hooks and health checks carries the service's
  name and the hook's, such as `sshd/ExecStartPre[0]`. A job someone
  started carries `jobs/` and the job's ID.
- **which stream** it was written to. Programs are meant to write errors
  to standard error, but many write everything there.
- **when** it was written, and which run of the service (its *job*) wrote it.

Log delivery to eventd is best effort: under load, downstream buffering
and forwarding can drop lines. A service can still slow down when it
writes output faster than peinit reads it, because writes to its output
pipe can block. See
[Service output and logging](~peios/services-and-jobs/output-and-logging).

### Events

An event is a record with named fields. Every event has a **type**, such
as `peinit.job.started` or `kacs.audit.access.checked`, and a
**source**, which says what recorded it:

| Source | What records it |
|---|---|
| Programs | System programs such as peinit, the service manager |
| Kernel | The kernel's event channel, KMES |
| Security | KACS, the kernel's access control |
| Registry | LCS, the kernel's registry |

Every event also carries the process and token that caused it, and the
boot it happened in. Its other fields depend on its type. A
`kacs.audit.access.checked` event, for example, says who asked, for
what, on what, and whether it was allowed.

Use events when you need the structured record of an operation or access
decision. eventd stores the events it receives and records detected loss,
but this is not a guarantee that every event survives: the kernel's event
buffers are finite and can overwrite events before a consumer reads them.
The kernel buffers do not persist across reboots; eventd provides stored
history. Check loss reports as well as the events themselves when accounting
for what happened. See [Auditing](~peios/auditing/overview) and the kernel
manual's [event failure modes](~peios/advanced-peios/peios-kernel/kmes/failure-modes).

### Metrics

A metric is a named number that a program measures again and again, such
as how many requests a server has answered or how full a disk is. Each
measurement is a *sample*. A metric can have several *series*, one for
each set of its labels: `eventd.store.bytes` has a series for each of
eventd's stores, labelled `store=logs`, `store=events` and so on.

Every metric is one of three types:

- a **counter** only goes up, such as requests answered, so what matters
  is how fast it rises;
- a **gauge** goes up and down, such as bytes in use;
- a **histogram** is a spread of measurements, such as how long requests
  took, read by its percentiles.

A program publishes metrics only under names it has been allowed to.
eventd publishes its own health as metrics named `eventd.*`. Like logs,
metrics are best effort.

## Who may read what

Every query to eventd runs as the person who asked. eventd checks what
they may read against its read policy, which grants reading by name: a log
origin, an event type or a metric name.

What a person may not read is **left out without comment**. eventd never
says that something was withheld, because saying so would itself tell
them something. An empty answer therefore does not prove that nothing
happened. Event Viewer also tries to read the policy and reports which
names it permits, restricts, or cannot determine. A restriction notice
does not prove that any hidden record exists; even unrestricted results
cover only stored, queryable records. See
[what you may not see](~peios/logs-and-events/event-viewer#what-you-may-not-see)
and the [missing-record checks](~peios/logs-and-events/find-missing-records).

## Where to look

- **On the desktop:** [Event Viewer](~peios/logs-and-events/event-viewer)
  shows events and logs, newest first, as they arrive, and charts metrics
  on dashboards of your own.
- **In a terminal:** `evctl` runs a query in eventd's query language and
  prints what comes back. See [Using evctl](~peios/evctl/using-evctl).
- **For incident review:** [Save incident event evidence](~peios/logs-and-events/save-incident-evidence)
  keeps a bounded query result with its diagnostics, completion status
  and context.
