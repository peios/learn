---
title: What the machine records
type: concept
description: eventd keeps three records of what happens on a Peios machine — logs, events and metrics — and shows each person only what they may read.
related:
  - peios/logs-and-events/event-viewer
  - peios/services-and-jobs/output-and-logging
  - peios/auditing/overview
---

A Peios machine keeps a record of what happens on it. One service,
**eventd**, receives that record, stores it and answers questions about it.
Nothing else on the machine stores logs, so there is one place to look.

## Three kinds of record

eventd keeps three kinds of record, which arrive by different routes and
answer different questions.

| Kind | What it is | Where it comes from |
|---|---|---|
| **Logs** | Lines of text that services and jobs write | The service manager, peinit, which reads every service's output and passes each line on |
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

Logs are best effort. Under heavy load some lines can be dropped, by
design, so that logging never slows the machine down. See
[Service output and logging](~peios/services-and-jobs/output-and-logging).

### Events

An event is a record with named fields. Every event has a **type**, such
as `job.started` or `access.denied`, and a **source**, which says what
recorded it:

| Source | What records it |
|---|---|
| Programs | System programs such as peinit, the service manager |
| Kernel | The kernel's event channel, KMES |
| Security | KACS, the kernel's access control |
| Registry | LCS, the kernel's registry |

Every event also carries the process and token that caused it, and the
boot it happened in. Its other fields depend on its type. An
`access.denied` event, for example, says who asked, for what, and on what.

Events are kept far more carefully than logs. The kernel holds them until
eventd has stored them, and if any are ever lost, eventd records that they
were. They are the record to trust when something has to be accounted
for. See [Auditing](~peios/auditing/overview).

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
them something. So an empty answer can mean "nothing happened" or "nothing
you may see happened". Event Viewer reads the policy too, and says which
of the two it is.

## Where to look

- **On the desktop:** [Event Viewer](~peios/logs-and-events/event-viewer)
  shows events and logs, newest first, as they arrive, and charts metrics
  on dashboards of your own.
- **In a terminal:** `evctl` runs a query in eventd's query language and
  prints what comes back. See [Using evctl](~peios/evctl/using-evctl).
