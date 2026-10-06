---
title: "notify.*"
description: "Every field the evman catalogue defines under notify: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `notify`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="notify.errno"></a>`notify.errno`

- **Type:** `int.errno`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The error number a service sent as `ERRNO=`, as a negative errno. Services
send it positive, by convention; this field holds it negated.

The field is the service's claim about itself, informational only; peinit
neither acts on nor retains it. peinit carries the raw text today under
`errno`, unparsed, and the protocol does not require it to be a number:
text that is not one cannot be carried here.

**Carried by:**

No event carries this field yet.

## <a id="notify.exit-status"></a>`notify.exit-status`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The exit status a service sent as `EXIT_STATUS=`, informationally. Not
the exit code of any process: a service may send it while still running,
and its real exit appears in `object.process.exit-code`. peinit carries
the raw text today under `exit_status`, unparsed.

**Carried by:**

No event carries this field yet.

## <a id="notify.progress.bounded"></a>`notify.progress.bounded`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Whether the progress a service or submitted job reported declares an end:
true for `PROGRESS=N/` and `PROGRESS=N/M`, false for a bare `PROGRESS=N`,
which counts with no end (PSPU §4.19). It is what tells a viewer to draw a
bar or to expect one rather than show a rising count.

True with `notify.progress.total` absent means the end is declared but not
yet known. Absent when no progress figure has been reported, as when a
service has sent only `PROGRESS_UNIT=`.

**Carried by:**

No event carries this field yet.

## <a id="notify.progress.current"></a>`notify.progress.current`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How far a service or submitted job has got, as it reported with
`PROGRESS=`: the count before any `/`. Its unit is
`notify.progress.unit`. It may fall from one record to the next; do not
read motion from the difference between two.

**Carried by:**

No event carries this field yet.

## <a id="notify.progress.total"></a>`notify.progress.total`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The end `notify.progress.current` is counting towards, as reported after
the `/` of `PROGRESS=`. At least 1, and never less than the current
value. The total may change between records, because a job that
rescans has learned something.

Absent when the service gave no total, and **absence alone does not say
whether one is coming**. `PROGRESS=N` counts with no end, while
`PROGRESS=N/` counts towards an end not yet known, and both leave this
field absent; `notify.progress.bounded` is what tells them apart.

**Carried by:**

No event carries this field yet.

## <a id="notify.progress.unit"></a>`notify.progress.unit`

- **Type:** `str.enum`
- **Values:** `bytes` · `items` · `percent`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

What `notify.progress.current` and `notify.progress.total` count, as
reported with `PROGRESS_UNIT=`. Absent when the service gave no unit.

**Carried by:**

No event carries this field yet.

## <a id="notify.status"></a>`notify.status`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The text a service sent as `STATUS=`: free text describing what it is
doing. The service's own words, unvalidated; never read it as a
statement by peinit.

**Carried by:**

No event carries this field yet.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
