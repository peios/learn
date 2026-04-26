---
title: Boot Partitioning
---

## Boot ID

Every record stored by eventd -- events, logs, and metrics -- carries a `boot_id`: a 16-byte GUID that uniquely identifies the boot during which the record was produced. The boot ID is assigned by peinit at each boot and communicated to eventd at startup.

The boot ID serves two purposes:

- **Partitioning.** Records from different boots are never interleaved in a meaningful sequence. KMES per-CPU sequence numbers reset to zero on each boot. Without a boot ID, sequence number 42 from boot A would be indistinguishable from sequence number 42 from boot B.
- **Lifecycle.** Retention can use boot ID to efficiently delete all data from old boots as a single operation, rather than scanning by timestamp.

## Scope

Boot ID is written to the `boot_id` column in all three stores:

- **Event store:** every row in the `events` table.
- **Log store:** every row in the `logs` table.
- **Metric store:** metrics do not carry boot_id per sample. The boot boundary is less meaningful for metrics because time series are continuous across restarts -- a gauge value is valid regardless of which boot produced it.

> [!INFORMATIVE]
> The log store includes boot_id because log output may have different meaning across boots (a service may emit different logs depending on boot-time configuration). The metric store omits per-sample boot_id because metric time series are inherently continuous -- a CPU usage reading at 42% is equally valid regardless of boot context. If boot-scoped metric queries are needed, the timestamp can be correlated with the boot ID from the event store's synthetic startup/shutdown events.

## Sequence uniqueness (events only)

Within a single boot, an event is uniquely identified by the tuple (`boot_id`, `cpu_id`, `sequence`). Across boots, `boot_id` provides the disambiguating dimension. The combination of all three fields is globally unique.

## Boot boundary detection

When eventd starts, it reads the current boot ID from peinit. If the boot ID differs from the boot ID of the most recently stored events (read from the shard databases), eventd has started in a new boot.

On a new boot, eventd MUST:

1. Reset all per-CPU sequence trackers to 0.
2. Record the new boot ID for all subsequent writes to the event and log stores.
3. Emit a synthetic `synthetic.startup` event with the new boot ID.

On a restart within the same boot (eventd crashed and was restarted by peinit), the boot ID matches and eventd MUST:

1. Restore per-CPU sequence trackers from the last persisted sequence numbers.
2. Continue writing with the existing boot ID.
3. Emit a synthetic `synthetic.startup` event noting the restart.
