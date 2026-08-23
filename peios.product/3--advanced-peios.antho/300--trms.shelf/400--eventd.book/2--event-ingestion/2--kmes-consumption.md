---
title: KMES Consumption
description: Discovering CPUs and attaching to their rings, the drain threads, copying, generation changes and sequence tracking.
---

## Attachment

At startup eventd discovers the CPU count by calling `kmes_attach` with
incrementing CPU identifiers from 0 until the call returns `EINVAL`.
Each successful call returns one file descriptor for that CPU's ring
buffer, and eventd maps each one. The mapping size is derived from the
`capacity` value the call reports, as PSPK defines it.

Attachment requires SeSecurityPrivilege in the effective token, which is
the privilege that grants an unfiltered view of every event on the
system. eventd holds it because it is the party that then applies
per-event access control on everything it stores (§7).

Discovering zero CPUs is a startup failure (§8.2). There is no
configuration for the CPU count and no way to attach to a subset.

## Drain threads

There is one drain thread per CPU, and each reads exactly one ring
buffer. A drain thread never reads another CPU's buffer, which is what
makes per-CPU sequence tracking a thread-local variable rather than
shared state.

Each thread follows the read protocol PSPK specifies:

- `read_pos` starts at `tail_pos` on first attachment, so eventd begins
  at the oldest surviving event rather than at the newest.
- The drain loop loads `write_pos` with acquire ordering, checks
  `tail_pos` for lapping, validates the event's structural integrity,
  and advances `read_pos` by `event_size`.
- After reading an event it re-reads `tail_pos` — the torn-read check —
  to detect that KMES overwrote the event while it was being copied.
- With nothing to read it uses the notification protocol, setting
  `need_wake` and waiting on the futex, rather than spinning.

## Copying

A drain thread copies the event — header and payload — into
process-local memory before it advances `read_pos`.

Nothing derived from the mapped region ever reaches a writer thread. The
region is producer-owned and KMES may overwrite any part of it the
moment `read_pos` moves past, so a pointer handed across the channel
would be a pointer into memory that another CPU is entitled to rewrite
before the writer gets to it.

The copy is bounded by the event's own `event_size`, and the drain
thread never reads beyond it.

## Generation changes

An administrator changing the ring buffer capacity causes KMES to
replace the buffers, which it signals by changing the `generation`
field. A drain thread checks it after each drain cycle, and on a change:

1. Records the sequence number of the last event it processed.
2. Calls `kmes_attach` again for its CPU, obtaining a descriptor for the
   resized buffer.
3. Maps the new buffer.
4. Unmaps the old one and closes the old descriptor.
5. Scans the new buffer for the first event whose sequence number
   exceeds the recorded one.
6. Resumes draining from there.

Each drain thread handles this independently. There is no barrier, no
coordination and no shared state, because each attaches only to its own
CPU's buffer — so a resize is a per-CPU event that happens to occur on
every CPU at roughly the same time.

The scan in step 5 is what makes the transition lossless in both
directions: no event is skipped, and none is written twice.

## Sequence tracking

Each drain thread holds the last sequence number it saw for its CPU. It
serves gap detection (§2.5) and resumption after a generation change or
a restart.

At startup, if committed rows already exist for the current boot, the
resume point for each CPU is derived from those rows:

```sql
MAX(sequence)
WHERE boot_id = current_boot_id
  AND cpu_id = cpu
  AND sequence IS NOT NULL
```

across **every readable event shard database**, historical shards
included. Historical shards can hold current-boot rows: an eventd
restarted within one boot under a smaller shard count leaves its
higher-numbered shards behind, and the events it wrote to them before
the restart are still that boot's events.

The `sequence IS NOT NULL` clause excludes synthetic events, which have
no sequence numbers (§2.6).

Committed rows are the authority. The metadata database holds sequence
checkpoints and the shutdown event records the same numbers (§3.5,
§8.4), but both are diagnostic: a checkpoint can be stale in exactly the
case that matters, where eventd died between its last commit and its
last checkpoint, and trusting it would mean re-reading events already
stored or skipping a gap.

With no prior rows for the current boot, the tracker starts at 0. The
first event on each CPU carries sequence number 1, so a tracker at 0
expects 1 and detects a gap correctly if the first event it sees is
later.
