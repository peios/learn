---
title: Boot Partitioning
---

## Boot ID

Every observability record stored by eventd -- events, logs, and raw metric samples -- carries a `boot_id`: a 16-byte GUID that uniquely identifies the boot during which the record was produced. The boot ID is assigned by peinit at each boot and communicated to eventd at startup. Derived metric rollups are boot-agnostic and do not carry a `boot_id`.

The boot ID serves two purposes:

- **Partitioning.** Records from different boots are never interleaved in a meaningful sequence. KMES per-CPU sequence numbers reset to zero on each boot. Without a boot ID, sequence number 42 from boot A would be indistinguishable from sequence number 42 from boot B.
- **Lifecycle.** Retention can use boot ID to efficiently delete all data from old boots as a single operation, rather than scanning by timestamp.

## Scope

Boot ID is written to the `boot_id` column in all three stores:

- **Event store:** every row in the `events` table.
- **Log store:** every row in the `logs` table.
- **Metric store:** every row in the `samples` table. The boot ID is not part of the metric series identity and is not stored on rollup rows.

> [!INFORMATIVE]
> The log store includes boot_id because log output may have different meaning across boots (a service may emit different logs depending on boot-time configuration). The metric store records boot_id per sample for tracking and filtering while keeping time series continuous across restarts. Rollups remain boot-agnostic scalar aggregates; boot-filtered metric queries use raw samples.

## Sequence uniqueness (events only)

Within a single boot, an event is uniquely identified by the tuple (`boot_id`, `cpu_id`, `sequence`). Across boots, `boot_id` provides the disambiguating dimension. The combination of all three fields is globally unique.

## Boot boundary detection

When eventd starts, it reads the current boot ID from peinit. It then searches all readable event shard databases for committed rows with that `boot_id`. If no committed rows exist for the current boot ID, eventd treats this as the first eventd start for this boot. If committed rows exist for the current boot ID, eventd treats this as a restart within the same boot.

On a new boot, eventd MUST:

1. Reset all per-CPU sequence trackers to 0.
2. Record the new boot ID for all subsequent writes to the event store, log store, and metric samples.
3. Emit a synthetic `synthetic.startup` event with the new boot ID.

On a restart within the same boot (eventd crashed and was restarted by peinit), eventd MUST:

1. Restore per-CPU sequence trackers from committed event rows in all readable event shard databases. For each CPU, the resume point is the maximum non-NULL `sequence` value for (`boot_id`, `cpu_id`) in the `events` table. CPUs with no committed rows for the current boot resume from 0.
2. Continue writing with the existing boot ID.
3. Emit a synthetic `synthetic.startup` event noting the restart.

Committed event rows are the authoritative source for sequence resumption. Metadata entries and synthetic shutdown payloads MAY record the same resume points for diagnostics, but eventd MUST NOT rely on them instead of scanning committed event rows during startup.
