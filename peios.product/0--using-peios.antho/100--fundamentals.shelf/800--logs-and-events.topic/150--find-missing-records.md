---
title: Find missing records
type: how-to
description: Check query scope, visibility, failures, retention and storage evidence before concluding that an expected record was never written.
related:
  - peios/logs-and-events/overview
  - peios/logs-and-events/event-viewer
  - peios/logs-and-events/save-incident-evidence
  - peios/services-and-jobs/output-and-logging
  - peios/evctl/using-evctl
---

An empty result does not establish that nothing happened. Work through
these checks in order, keeping the observations as you go. Preserve
relevant records before changing retention or cleaning up storage.

## 1. Check the service, time and filters

- For a service, open **Logs…** from Services Manager and confirm the
  service name and the incident time. Match the job and boot when
  inspecting a record; a restart has a different job ID. Use
  [Find service logs](~peios/services-and-jobs/output-and-logging#find-the-failed-run)
  for the service-run workflow. A service using `TTYPath` writes to its
  terminal instead of having its output captured for eventd.
- Events and Logs start with the **last 24 hours**. Choose a range that
  includes the incident, then use **Show older** to page back. **any time**
  removes the time restriction; it cannot bring back removed records.
- Check **From**, **Containing** and **Errors only** for logs, or **Type**
  and **Source** for events. Remove unintended restrictions and press
  **Enter** or **Apply** for typed filters. Standard error is a stream,
  not proof that a line describes an error.

For exact controls and paging limits, see
[Event Viewer](~peios/logs-and-events/event-viewer#the-time-range-and-applying-a-filter).

## 2. Read the visibility notice

Check the bottom-right notice described in
[What you may not see](~peios/logs-and-events/event-viewer#what-you-may-not-see).
It reports what the read policy allows for names, not whether matching
hidden records exist. **Some logs may be hidden from you** means that
the policy itself could not be read. Even an unrestricted policy cannot
establish complete history: the data must still have been captured,
retained and available to the query.

Record the notice. If the required names are restricted or the policy
cannot be determined, ask an administrator to check the relevant policy
and records; do not change permissions just to make an empty result
disappear.

## 3. Distinguish a failed query from an empty one

Keep any access refusal, timeout or storage error. A failed query does
not establish the absence of matching records. A
[query timeout](~peios/advanced-peios/eventd/failure-modes/losing-events#query-timeouts)
means the query did not finish, not that ingestion lost data. After
recording the error, a narrower time range can help isolate the problem.

In a terminal, retain `evctl`'s diagnostics on standard error as well as
its result. Its [result-commitment rules](~peios/evctl/using-evctl#result-commitment)
explain why an error before the initial result completes invalidates
that partial result. If live following stops, record the notice before
using **Show the newest** to resume; that action alone does not establish
what happened in the gap.

## 4. Check the retention settings

Open Event Viewer's **Settings**, then **Keeping records**, and note the
current values or defaults without changing them. Anyone may inspect
these settings; changing them requires the separate settings permission,
granted to administrators by default.

The [documented defaults](~peios/advanced-peios/eventd/configuration-keys#retention)
are 30 days for events, 14 for logs and 90 for metric samples. Events and
logs have no size limit by default; metrics default to 1 GiB. These are
retention limits, not a minimum guaranteed history. Both age and any
enabled logical-live-size limit are enforced, so size pressure can
remove younger records.

[Event retention](~peios/advanced-peios/eventd/event-storage/retention#size)
can remove a whole earlier boot, including its loss records. Logs and
metrics instead lose their oldest entries or samples under size pressure;
see [log retention](~peios/advanced-peios/eventd/log-storage/retention#age-and-size)
and [metric retention](~peios/advanced-peios/eventd/metric-storage/retention#the-pass).
Present settings alone cannot establish which records were previously
removed.

## 5. Look for loss or an unavailable store

Look around the incident time for `eventd.events.lost`,
`eventd.store.quarantined`, and eventd's own log errors. If available,
its [health metrics](~peios/advanced-peios/eventd/metric-storage/health-metrics#the-series)
also show recorded loss, write errors and retention deletions.

- A loss record establishes detected loss, not complete accounting.
  [Power loss](~peios/advanced-peios/eventd/failure-modes/power-loss) can
  destroy the final volatile event batch without a loss record. Logs and
  metrics have weaker durability, and full socket queues can refuse their
  data [without a health count](~peios/advanced-peios/eventd/failure-modes/losing-events#ingestion-backpressure).
- A [quarantined store](~peios/advanced-peios/eventd/event-storage/database-lifecycle#quarantine)
  is replaced by an empty one. The quarantined files may be the only copy
  of the earlier records. Query-time corruption instead
  [fails the affected query](~peios/advanced-peios/eventd/failure-modes/storage-failure#corruption).
- An unreadable or invalid [historical shard](~peios/advanced-peios/eventd/event-storage/database-lifecycle#historical-shards)
  can be logged and excluded from queries for that run without preventing
  startup. A running eventd therefore does not establish that every old
  store is being queried.

These observations narrow the cause; absence of a loss or quarantine
record does not prove that the history is complete.

## 6. Preserve evidence before cleanup

Keep the service, job and boot identifiers, incident time range, filters,
visibility notices, exact errors, and retention values. Use **Copy** on
relevant Event Viewer rows to keep all fields, or retain completed
`evctl` results together with their query and diagnostics. Follow
[Save incident event evidence](~peios/logs-and-events/save-incident-evidence)
for private output files, completion checks and a bounded capture.

Leave quarantined files intact and involve the administrator responsible
for recovery. eventd does not automatically repair them. Do not delete,
rename or edit database files as a diagnostic experiment, or retry a
destructive operation before preserving the evidence it may remove.

Retention measures **logical live size**, not filesystem usage. Deleting
records frees pages for reuse; it does not immediately shrink the database
file, and eventd never automatically runs `VACUUM`. See
[Reclamation](~peios/advanced-peios/eventd/event-storage/retention#reclamation)
before planning space recovery; these checks are not a database-repair
or live-maintenance procedure.
