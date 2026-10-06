---
title: Writing evman pages
type: how-to
description: How to describe your package's events so evman can explain them. You ship a .evman fragment in /usr/share/evman/; this is its format, what to define and what to reference, the lint workflow, and the rules the tools won't catch for you.
related:
  - peios/event-tools/evman
  - peios/sdk-events/naming-and-shaping-events
  - peios/pgss/events/the-catalogue
  - peios/documenting-configuration/writing-regman-pages
  - pekit/recipes/packages
---

An event record carries a type name and a MessagePack payload, but never its *meaning* — it does not say that `outcome.reason` is only present on failure, or which of two masks a field holds. That knowledge ships with the software that writes the event, as documentation [`evman`](~peios/event-tools/evman) reads. From the operator's side this is the event manual; from yours, the package author's, it is a file you write and install.

This page is how you write one. It assumes you have already designed your events — their types, fields and tiers — as [Naming and shaping your events](~peios/sdk-events/naming-and-shaping-events) describes. The normative rules are [PGSS §6.10](~peios/pgss/events/the-catalogue); this page applies them.

## Where the documentation lives

`evman` reads a drop-in directory, `/usr/share/evman/`. Each `*.evman` file in it is one **fragment**, named for the component that ships it:

```
/usr/share/evman/
    kernel.evman                # the platform fragment: the shared field vocabulary
    kacs.evman
    org.example.backup.evman    # yours
```

A package ships one fragment per component, describing every event type that component writes and every field it defines. There is no central index to register with and no install-time hook: dropping the file in is the whole act, and removing it on uninstall is the whole undo.

Ship it the way you ship any other file. A hand-written fragment kept beside the recipe maps straight into the payload from the package file's `[files]` table:

```toml
[files]
"@recipe:org.example.backup.evman" = "usr/share/evman/org.example.backup.evman"
```

See [Packages](~pekit/recipes/packages) for ref resolution.

> [!NOTE]
> The fragment is not optional documentation. The catalogue is the definition of what may be emitted: an emitter MUST NOT write a field the catalogue does not define (PGSS §6.4), and MUST describe every event type it writes. A package whose events have no fragment is emitting undefined events.

## The shape of a fragment

A fragment is a sequence of **records**. Each begins with an anchor line — three hyphens, a space, the record kind, a space and the name — then header lines, a blank line, and prose:

```
--- field object.org.example.backup.snapshot.id
type: bin.guid

The snapshot an event concerns, by the GUID the backup tool assigned it.
```

There are three kinds of record:

| Kind | Defines | Header keys |
|---|---|---|
| `field` | One field path | `type`, and for an enumeration `values` and `closed` |
| `group` | A named set of fields that travel together | `include:` lines, one field each |
| `event` | One event type | `tier`, `gating` if anything decides which occurrences are recorded, `cardinality` if one occurrence makes more than one record |

The prose's **first sentence is the summary** `evman` shows in its indexes and `-k` results, so make it a complete sentence that stands on its own. Inline markup is `**bold**` and `` `code` `` only. The full key tables, including the rarely needed `asserted` and `carried`, are in [§6.10](~peios/pgss/events/the-catalogue).

### Event records list their fields

After an event's prose come the fields it carries, one per line, each saying when it is present:

```
field: object.file.path                       required
field: object.file.size                       when outcome.success == true
field: outcome.reason                         when outcome.success == false
  values: disk-full | source-unreadable | cancelled
  closed: false
  Why the snapshot was not written.
```

- **Presence** is `required`, `optional`, or `when` and a condition on another field the event carries.
- **An indented paragraph** after a `field:` line is a *gloss*: what the field means in this event. Use it wherever the general definition is broader than what this event puts there. A gloss may narrow a definition and must not contradict it.
- **Indented `values:` and `closed:` lines** declare the values of a field whose definition leaves them to each event. `outcome.reason` is the common case: every event has its own reasons.
- **`include: <group>`** carries every field of a group at once.

## Define your own fields; reference everyone else's

This is the rule that matters most, and the one a new author most often gets wrong.

**A `--- field` record defines a field. A `field:` line on an event carries it.** You carry any field defined anywhere — `subject.token.sid`, `object.file.path`, `outcome.success` are all defined in the platform fragment, and your events reference them freely. You *define* a field only when no existing one has the meaning you need, and then only beneath your own package name, under the role it describes:

```
--- field object.org.example.backup.snapshot.id
```

Two fragments defining the same path is an error, and so is redefining a standard field "to be safe": one value with two names is a value a security descriptor can deny under one and leak under the other. Before defining anything, look for it:

```bash
evman object.file          # what is defined under object.file?
evman -k snapshot          # does anything already mean this?
```

If you find a field every package like yours would want and nobody defines, that is a gap in the shared vocabulary worth reporting rather than working around.

## Enumerations declare their values

A field whose type is `str.enum` or `uint.enum` lists its values and says whether the list is closed:

```
--- field object.org.example.backup.snapshot.kind
type: str.enum
values: full | incremental | differential
closed: true

Which kind of snapshot was taken. ...
```

- A `str.enum` value is a kebab-case string. A `uint.enum` value is a number and the name it renders as: `0 None | 512 Protected`.
- `closed: true` promises that no value is added without a new version of the field. Consumers rely on it, so only claim it when the set is genuinely complete; otherwise say `false`, and consumers will cope with a value they have not seen.
- Take the values from your code, not from memory. Nothing checks that the list matches what your program writes.

## A complete fragment

```
--- field object.org.example.backup.snapshot.id
type: bin.guid

The snapshot an event concerns, by the GUID the backup tool assigned it.
Stable for the life of the snapshot, so it joins a snapshot's creation to
its later verification and deletion.

--- event org.example.backup.snapshot.created
tier: standard

A snapshot was written, or an attempt to write one failed.

field: object.kind                            required
  Always `file`.
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

Only `object.org.example.backup.snapshot.id` is defined here. Every other field is the platform's, and the event references it.

## The lint workflow

```bash
evman lint /usr/share/evman/*.evman org.example.backup.evman
```

Lint your fragment **together with the installed ones**. The rules that matter most — every referenced field is defined somewhere, no path is defined twice, no path is both a value and a map — can only be checked across the whole catalogue, and your fragment references fields defined in others. `evman lint` checks every rule of [§6.10](~peios/pgss/events/the-catalogue), prints each finding as `file:line: rule N: message`, and exits non-zero if there is any. A clean catalogue prints nothing.

Wire it into your build so a broken fragment fails the build rather than shipping.

### Preview before you ship

`evman` honours `EVMAN_DIR`, so you can see exactly what an operator will see without installing anything. Copy the installed fragments and yours into one directory and point it there:

```bash
mkdir -p /tmp/evman && cp /usr/share/evman/*.evman org.example.backup.evman /tmp/evman/
EVMAN_DIR=/tmp/evman evman org.example.backup.snapshot.created
EVMAN_DIR=/tmp/evman evman object.org.example.backup
```

## Rules the tools won't catch

`evman lint` checks structure, names, definitions and references. These it does **not** check, and they are on you:

- **That a value list is right.** Lint checks that an enumeration *has* values, not that they are the ones your program writes.
- **That a condition is true.** `when outcome.success == false` is checked for naming a field the event carries, not for matching when your program actually writes the field.
- **That the gloss agrees with the definition.** A gloss may narrow a field's meaning, never change it. If you find yourself writing a gloss that redefines a field, you want a different field.
- **That the tier is honest.** `essential` is for events that are extremely important and rare, or already governed by their own configuration; it cannot be switched off. Packages submitted to the Peios package repository are checked for it by hand.
- **Never start a prose line with `--- ` and a word.** It is an anchor: it starts a new record and silently splits yours in two.

## See also

- [evman](~peios/event-tools/evman) — the operator's view: reading an event card, a field card, and the `-k` search.
- [Naming and shaping your events](~peios/sdk-events/naming-and-shaping-events) — designing the events this page documents.
- [The Catalogue](~peios/pgss/events/the-catalogue) — the normative format and rules.
- [Writing regman pages](~peios/documenting-configuration/writing-regman-pages) — the same job for your registry keys.
