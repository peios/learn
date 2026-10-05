---
title: Naming and shaping your events
type: how-to
description: Design an event before you emit it — decide it is an event, name its type under your package, choose fields from the catalogue, encode the values, record the outcome, declare a tier, and describe it all in an evman fragment.
related:
  - peios/pgss/events/scope-and-roles
  - peios/pgss/events/event-types
  - peios/pgss/events/fields
  - peios/pgss/events/the-catalogue
  - peios/sdk-events/emitting-events
---

Every event on Peios follows one naming scheme and one field vocabulary,
so that an operator can find your events with the same queries and
security descriptors they use for everyone else's. This guide walks
through designing one event, from deciding that it should be an event to
describing it for the catalogue. The rules themselves are in
[PGSS Events](~peios/pgss/events/scope-and-roles); this page applies
them.

The running example is a backup tool, packaged as `org.example.backup`,
that writes a snapshot archive and wants to record each one.

## Decide that it is an event

Ask two questions, in order:

1. **Does an operator care?** If only the tool's developers would read
   it, write a log line instead.
2. **Does one instance matter on its own?** If it does, it's an event.
   If only the trend matters — snapshots per hour, bytes per day — it's
   a metric.

An operator wants to know that last night's snapshot failed, so each
snapshot is an event. See
[Events, logs and tiers](~peios/pgss/events/events-logs-and-tiers).

## Name the event type

An event type is your package name, then one or more nouns from general
to specific, then a past-tense verb:

```text
org.example.backup.snapshot.created
```

- **The root is your package name**, split at its dots. Short roots such
  as `kacs` and `peinit` are reserved to platform components.
- **Add a noun only where someone would write a policy on the set
  beneath it.** `org.example.backup.snapshot` groups everything about
  snapshots, which an administrator might plausibly switch off or grant
  access to as a whole.
- **End with what happened**, in the past tense: `created`, `started`,
  `ended`, `deleted`.
- **Use one type for success and failure.** A failed snapshot is still
  `org.example.backup.snapshot.created`, carrying
  `outcome.success = false`. Don't add a `snapshot.failed` type.
- **Use lowercase and kebab-case** within a segment: `copied-up`, never
  `copied_up` or `copiedUp`.

See [Event types](~peios/pgss/events/event-types) for the full grammar.

## Choose the fields

A field is named for the part it plays, then what it is, then which
property:

| Field | Value in this event |
|---|---|
| `object.kind` | `file` |
| `object.file.path` | The snapshot archive written |
| `object.file.size` | Its size in bytes |
| `operation.duration` | How long the snapshot took |
| `outcome.success` | Whether it was written |
| `outcome.reason` | Why not, when it wasn't |
| `outcome.errno` | The error number, when there is one |

**Look a field up before you invent one.** The standard fields cover
almost everything an event carries: who acted (`subject.*`), what was
acted on (`object.*`), where something came from or went to (`source.*`
and `destination.*`), and how it turned out (`outcome.*`). The catalogue
of every defined field is installed in `/usr/share/evman/` and listed in
the Events reference book.

A few things never go in your payload:

- **Anything the header already carries.** The kernel stamps the time,
  the sequence number and your token and process identities on every
  event. Don't write a `timestamp`.
- **A principal's name.** Carry its SID in `subject.token.sid` or
  similar. Consumers resolve names when they read the record.
- **A field you have no value for.** Leave the key out rather than
  writing nil, `""` or `0`.

If your event genuinely needs a field the catalogue doesn't have, put it
beneath your package name, under the role it describes:

```text
object.org.example.backup.snapshot.id
```

This should be rare. If you find a field that every backup tool would
want, that's a gap in the standard set worth reporting.

## Encode the values

Each field's type fixes its wire form. The ones you'll meet most:

| Kind of value | Write it as |
|---|---|
| A SID | The binary SID, never an SDDL string |
| A GUID | 16 raw bytes, never a hyphenated string |
| A time | Nanoseconds since the Unix epoch, as an unsigned integer |
| A duration | Nanoseconds, as an unsigned integer |
| A yes or no | A MessagePack boolean, never the string `"true"` |
| One of a fixed set | A kebab-case string: `disk-full`, not `2` or `DISK_FULL` |

The full table is in [Values](~peios/pgss/events/values).

## Build the payload

A dotted field path is a chain of nested maps: `object.file.path` is
`{object: {file: {path: …}}}`. Never write a key containing a dot; it
becomes a different field that no query can reach.

```c
peios_mp_writer *w = peios_mp_writer_new();

peios_mp_write_map(w, 3);                       /* object, operation, outcome */

peios_mp_write_str(w, "object", 6);
peios_mp_write_map(w, 2);                       /* kind, file */
peios_mp_write_str(w, "kind", 4);
peios_mp_write_str(w, "file", 4);
peios_mp_write_str(w, "file", 4);
peios_mp_write_map(w, 2);                       /* path, size */
peios_mp_write_str(w, "path", 4);
peios_mp_write_str(w, path, path_len);
peios_mp_write_str(w, "size", 4);
peios_mp_write_uint(w, size_bytes);

peios_mp_write_str(w, "operation", 9);
peios_mp_write_map(w, 1);
peios_mp_write_str(w, "duration", 8);
peios_mp_write_uint(w, elapsed_ns);

peios_mp_write_str(w, "outcome", 7);
peios_mp_write_map(w, 1);
peios_mp_write_str(w, "success", 7);
peios_mp_write_bool(w, true);
```

When the snapshot fails, the same type carries the reason instead of the
size:

```c
peios_mp_write_str(w, "outcome", 7);
peios_mp_write_map(w, 3);
peios_mp_write_str(w, "success", 7);
peios_mp_write_bool(w, false);
peios_mp_write_str(w, "reason", 6);
peios_mp_write_str(w, "disk-full", 9);
peios_mp_write_str(w, "errno", 5);
peios_mp_write_int(w, -ENOSPC);
```

`outcome.reason` is for filtering, so it's a value from a fixed set. If
you want to tell a person more, add `outcome.detail` as free text; nothing
parses it. See [Outcomes](~peios/pgss/events/outcomes).

[Emitting events](~peios/sdk-events/emitting-events) covers sending the
finished payload.

## Choose a tier

Every event type declares how much it matters to an operator:

| Tier | Use it for |
|---|---|
| `standard` | What an administrator reviews: lifecycle, configuration, failures. Most events. |
| `verbose` | Detail for an active investigation. Off unless switched on. |
| `debug` | For your own developers. Off unless switched on. |
| `essential` | Extremely important and rare, or already governed by its own configuration. Never switched off. |

A snapshot record is `standard`. Reserve `essential` for the two reasons
in its row; a package submitted to the Peios package repository is
checked for it.

Administrators switch event types on and off in the emission policy,
under `Machine\Generic\Events`. Your types live under
`Machine\Generic\Events\org\example\backup`, and an event type that is
switched off is never written. See
[Emission policy](~peios/pgss/events/emission-policy).

## Describe it in a fragment

Ship a fragment describing every event type you write and every field
you define, installed as `/usr/share/evman/org.example.backup.evman`:

```text
--- field object.org.example.backup.snapshot.id
type: bin.guid

The snapshot an event concerns, by the GUID the backup tool assigned it.

--- event org.example.backup.snapshot.created
tier: standard

A snapshot was written, or an attempt to write one failed.

field: object.kind                            required
field: object.file.path                       required
  The snapshot archive.
field: object.file.size                       when outcome.success == true
field: object.org.example.backup.snapshot.id  required
field: operation.duration                     required
field: outcome.success                        required
field: outcome.reason                         when outcome.success == false
  values: disk-full | source-unreadable | cancelled
  closed: false
  Why the snapshot was not written.
field: outcome.errno                          optional
```

You define only your own field. The standard ones are referenced, never
redefined: two fragments defining the same field is an error, because one
value with two names can be denied under one and read under the other.
The format and its rules are in
[The catalogue](~peios/pgss/events/the-catalogue).

## If your program guards access to something

A daemon that decides who may use its own objects doesn't emit its own
"access denied" event. It makes the decision through the kernel's access
check and passes the object's identity along, so that the kernel's audit
records the decision like any other. See
[Access decisions](~peios/pgss/events/access-decisions).

## Where to go next

- **[Emitting events](~peios/sdk-events/emitting-events)**: send the
  payload, singly or in batches.
- **[PGSS Events](~peios/pgss/events/scope-and-roles)**: the rules this
  page applies, in full.
