---
title: Boot Partitioning
---

## Boot ID

Every event, gap record, and synthetic event stored by eventd carries a `boot_id` -- a 16-byte GUID that uniquely identifies the boot during which the record was produced. The boot ID is assigned by peinit at each boot and communicated to eventd at startup.

The boot ID serves two purposes:

- **Partitioning.** Records from different boots are never interleaved in a meaningful sequence. KMES per-CPU sequence numbers reset to zero on each boot. Without a boot ID, sequence number 42 from boot A would be indistinguishable from sequence number 42 from boot B.
- **Lifecycle.** Retention can use boot ID to efficiently delete all data from old boots as a single operation, rather than scanning by timestamp.

## Sequence uniqueness

Within a single boot, an event is uniquely identified by the tuple (`boot_id`, `cpu_id`, `sequence`). Across boots, `boot_id` provides the disambiguating dimension. The combination of all three fields is globally unique.

## Boot boundary detection

When eventd starts, it reads the current boot ID from peinit. If the boot ID differs from the boot ID of the most recently stored events (read from the shard databases), eventd has started in a new boot.

On a new boot, eventd MUST:

1. Reset all per-CPU sequence trackers to 0.
2. Record the new boot ID for all subsequent writes.
3. Emit a synthetic `eventd.startup` event with the new boot ID.

On a restart within the same boot (eventd crashed and was restarted by peinit), the boot ID matches and eventd MUST:

1. Restore per-CPU sequence trackers from the last persisted sequence numbers.
2. Continue writing with the existing boot ID.
3. Emit a synthetic `eventd.startup` event noting the restart.
