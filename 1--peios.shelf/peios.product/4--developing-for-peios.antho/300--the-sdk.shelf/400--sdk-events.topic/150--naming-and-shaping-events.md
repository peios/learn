---
title: Naming and Shaping Events
type: how-to
description: Design event types, fields, outcomes, and tiers before implementing an emitter.
---

Design an event around an occurrence an operator needs to identify,
query, or investigate. A shared naming scheme and field vocabulary let the
same filters and access policies work across components and language SDKs.

The example is a backup package named `org.example.backup`. It records each
attempt to create a snapshot archive. The
[event specification](~specifications/pgss/events/scope-and-roles) owns the
rules; this guide applies them to an emitter's design.

## Before you start

- Identify the package that owns the event and the operation it describes.
- Inspect the installed event catalog with `evman` from Peiosutils.
- Identify which facts your component observes and which it receives as
  claims.

## Choose an event rather than a log or metric

1. Ask whether an operator would act on the information. Developer narrative
   belongs in a log.
2. Ask whether one occurrence matters by itself. If only the trend matters,
   publish a metric instead.

A failed snapshot matters individually, so the backup attempt is an event.
The daily amount of backed-up data is a metric. A trace of internal function
calls is developer logging. See
[Event Classification and Tiers](~specifications/pgss/events/events-logs-and-tiers).

## Name the operation

1. Start with the owning package name.
2. Add nouns from general to specific where the grouping supports a useful
   filter or policy boundary.
3. End with a past-tense description of the operation:

   ```text
   org.example.backup.snapshot.created
   ```

Use one type for success and failure. A failed creation still uses this type,
with `outcome.success = false`; do not add a parallel `snapshot.failed` type.
Use lowercase kebab-case segments, such as `copied-up`. Short platform roots,
such as `kacs`, are reserved. Package-name roots and the remaining segments
have their own grammar in [Event Types](~specifications/pgss/events/event-types).

## Reuse the field vocabulary

1. Search existing definitions before adding fields:

   ```sh
   evman object.file
   evman -k snapshot
   ```

2. Choose fields by their role: `subject` for who acted, `object` for what
   was acted on, `source` and `destination` for endpoints, and `outcome` for
   the result.
3. If no existing field has the required meaning, define a field beneath
   the owning package name and its role.

The snapshot uses shared fields plus one package-owned identifier:

| Field | Meaning in the snapshot event |
|---|---|
| `object.kind` | `file` |
| `object.file.path` | Archive path |
| `object.file.size` | Archive size in bytes, present on success |
| `object.org.example.backup.snapshot.id` | Stable snapshot identifier |
| `operation.duration` | Elapsed nanoseconds |
| `outcome.success` | Whether creation succeeded |
| `outcome.reason` | A declared reason when it failed |
| `outcome.errno` | Negative error number when applicable |

The package owns `object.org.example.backup.snapshot.id`; it references the
other definitions rather than redefining them. If many components need the
same missing concept, propose a shared field instead of giving it several
incompatible names.

Do not duplicate the timestamp, sequence, or identity fields already stamped
in the event header. Use binary security identifiers for principals rather
than account names. Omit a field for which no value is available; do not
substitute nil, an empty string, or zero. A real zero, such as an empty file's
size, remains a meaningful value.

## Match the declared wire types

Choose the encoding from the catalog definition, not from how a value is
displayed:

| Value | MessagePack encoding |
|---|---|
| Security identifier (SID) | Binary SID bytes |
| Globally unique identifier (GUID) | 16 raw bytes |
| Timestamp | Unsigned nanoseconds since the Unix epoch |
| Duration | Unsigned nanoseconds |
| Boolean | Boolean value |
| String enumeration | Declared kebab-case string |
| Numeric enumeration | Declared unsigned numeric value |
| Error number | Signed negative integer |

A numeric enumeration is not interchangeable with a string enumeration.
Follow the declared field type and its list of values. See
[Values](~specifications/pgss/events/values) for the full encoding rules.

Represent dotted paths as nested maps. `object.file.path` means an `object`
map containing a `file` map containing a `path` key. A literal key named
`object.file.path` is not that hierarchy. The package-owned identifier has
its own nested `object` → `org` → `example` → `backup` → `snapshot` → `id`
path.

## Record the outcome

1. Set `outcome.success` to the result of the operation.
2. On failure, supply a declared `outcome.reason`, such as `disk-full`.
3. Include `outcome.errno` only when an error number applies. Record its
   negative form, such as `-ENOSPC`.

The reason is a stable filtering value. Free-form explanation belongs in
`outcome.detail` when the catalog allows it; consumers should not parse that
text as a replacement for the reason. Describe required and conditional
fields in the fragment so both successful and failed attempts remain valid.
See [Outcomes](~specifications/pgss/events/outcomes).

## Choose the tier and apply policy

Use `standard` for ordinary operational records, including this snapshot.
Use `verbose` for investigation detail and `debug` for developer detail;
those tiers are off by default. Reserve `essential` for rare, critical
occurrences or events already governed by their own configuration, such as
access auditing. Essential does not mean that every program's diagnostics
are unconditionally important.

Emission policy is rooted at `Machine\Generic\Events`, with one key per
segment. This package's subtree is
`Machine\Generic\Events\org\example\backup`. Check policy before building
and emitting a nonessential record. Consumer-side filtering does not replace
that decision. Read [Emission Policy](~specifications/pgss/events/emission-policy)
for inheritance, failure handling, and interactions with other audit controls.

## Publish the definition and check the result

1. Describe the event and package-owned field in an `.evman` fragment.
2. Specify the tier and each field's required, optional, or conditional
  presence.
3. Lint it with the intended catalog and test actual encoded events against
  it.
4. Include the fragment in the package alongside the emitter.

[Writing evman Pages](~peios/developing-for-peios/documenting-events/writing-evman-pages)
contains the matching snapshot fragment and the validation workflow. Keep it
as the format example rather than maintaining a second copy here.
[Emitting Events](~peios/sdk-events/emitting-events) builds the corresponding
payload with the C SDK and explains individual and batch submission.

A well-formed MessagePack value is not necessarily a catalog-conforming event.
Check that successful and failed fixtures contain every required field with
the declared type, that absent values are omitted, and that queries can reach
the nested paths. A successful encoding or emission call does not prove those
semantic properties.

If your daemon guards access to its own objects, pass an audit context to the
kernel access check instead of inventing a competing access-denial event.
[Access Decisions](~specifications/pgss/events/access-decisions) explains how
the descriptor and audit policy control those records.
