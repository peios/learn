---
title: Exit and Shutdown
description: What ends the loregd process, what pointedly does not, and what happens to the data in each case.
---

## What ends the process

loregd exits when any of the following happens:

- **The kernel closes the registry device.** Reading from
  `/dev/pkm_registry` returns end-of-file, the request loop returns, and
  loregd shuts down cleanly with status 0. This is the normal path when
  the registry subsystem goes away.
- **A termination signal arrives.** `SIGTERM` and `SIGINT` are trapped.
  The handler closes the device, which unblocks the read loop and
  produces the same clean shutdown as above. This is how the service
  manager stops loregd.
- **A request cannot be framed.** If a message read from the device
  cannot be parsed as an RSI request, loregd treats it as unrecoverable
  and exits non-zero.
- **Startup fails.** Any error in §2.2 is fatal.

On shutdown, in-flight requests are drained before the process exits
(§4.2), and every hive's read connections and write connection are
closed.

## What does not end the process

A storage failure during request handling does **not** terminate loregd.
Errors from SQLite while serving a request — including I/O errors — are
converted into an `RSI_STORAGE_ERROR` response and the daemon carries on
serving. There is no corruption detector and no disk-full detector that
takes the process down; a database that has become unreadable will
produce a stream of storage errors rather than an exit.

> [!NOTE]
> This is worth knowing when diagnosing a system whose registry has
> started failing: the symptom is failing operations, not a dead daemon,
> and loregd will still be running and still registered.

## What happens to the data

Persistent data is durable at the point each transaction commits;
SQLite finalises any outstanding WAL state as the connections close.

Volatile data does not survive. The in-memory databases holding volatile
keys are destroyed with the process (§3.3), which is the entire point of
volatility. When the kernel observes the source disconnect, it marks
every hive loregd served as unavailable.
