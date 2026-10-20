---
title: The Catalogue
description: Where event and field definitions live — fragments in /usr/share/evman/ — the fragment format and its three record kinds, the platform fragment that holds the generic roots, and the rules every fragment must pass.
---

The catalogue is the single source of every event type and field
definition. Everything else that lists them — reference documentation,
a viewer's field picker, a policy editor — is generated from it or
checked against it.

## Fragments

An emitter MUST describe every event type it writes, and every field it
defines, in a **fragment**: a UTF-8 text file installed in
`/usr/share/evman/` with the extension `.evman`. A package installs one
fragment per component it ships, named for the component.

The **platform fragment**, `/usr/share/evman/kernel.evman`, defines the
generic roots of §6.4 and their common fields. A conforming system has
it.

A consumer that reads the catalogue reads every `.evman` file in
`/usr/share/evman/`, and no subdirectory.

## Format

A fragment is a sequence of records. Each record begins with an anchor
line of three hyphens, a space, the record kind, a space and the name it
defines:

```text
--- field subject.token.sid
--- group subject
--- event kacs.audit.access.checked
```

After the anchor come header lines of the form `key: value`, one per
line, then a blank line, then prose: the record's description. The
prose's first sentence is a complete summary of it. Inline markup in
prose is limited to `**bold**` and `` `code` ``.

### Field records

| Key | Required | Value |
|---|---|---|
| `type` | Yes | The field's type (§6.5) |
| `values` | For an enumeration | The values, separated by `\|`, or the name of the reason-code family they are drawn from |
| `closed` | For an enumeration | `true` if no value may be added without a new version of the field |
| `asserted` | No | `true` if the value may be supplied by userspace on a kernel-originated record (§6.7) |
| `carried` | No | `header` for a header field (§6.4); absent for a payload field |

### Group records

A group names a set of fields that always travel together, so that
events can include the set rather than list it. Its header lines are
`include:` lines, one field path each.

### Event records

| Key | Required | Value |
|---|---|---|
| `tier` | Yes | The event type's tier (§6.8) |
| `gating` | If any | What decides which occurrences are recorded |
| `cardinality` | No | How many records one occurrence produces, where that is not one |

After the prose come the fields the event carries, one per line:

```text
include: subject
field: object.kind              required
field: object.file.path         when object.kind == file
field: access.granted           required
  The mask this check granted.
```

`include:` names a group. `field:` names a field, followed by when it is
present: `required`, `optional`, or `when` and a condition on another
field of the record. An indented paragraph after a `field:` line is a
**gloss**: what the field means in this event. A gloss MAY narrow the
field's definition and MUST NOT contradict it.

Where a field's definition leaves its values to the event, as
`outcome.reason` does (§6.6), the event declares them with indented
`values:` and `closed:` lines directly after the `field:` line, in the
form a field record uses:

```text
field: outcome.reason           when outcome.success == false
  values: disk-full | source-unreadable | cancelled
  closed: false
  Why the snapshot was not written.
```

## Rules

Every fragment MUST pass these rules, checked across the whole catalogue:

1. Every path a `field:` or `include:` line names is defined.
2. No path is defined by two fragments, and no path is defined twice in
   one.
3. No path is defined both as a value and as a map (§6.4).
4. Every event type a fragment defines begins with a root that fragment
   owns: a platform root listed against its component in §6.A, or its
   package's name.
5. A platform component's fragment defines fields only in the subtrees
   and domains of things it alone knows about (§6.4). Any other fragment
   defines fields only beneath its own package name below a role (§6.4).
6. Every name matches the grammar of §6.3 and §6.4, and every event
   type's last segment is a verb in the past tense.
7. Every enumeration declares its values or names its reason-code
   family, and says whether it is closed.
8. Every event type declares a tier, and an event type with gating
   declares it.
9. An event type that carries a `uint.mask` field carries `object.kind`
   (§6.5).

A tool that reads the catalogue SHOULD report every rule a fragment
breaks. A consumer that acts on the catalogue — one that decides access,
builds a field tree for a descriptor, or validates payloads against it —
MUST NOT treat a fragment that breaks rule 1, 2 or 3 as defining
anything. A tool that only displays the catalogue MAY show such a
fragment's records, provided it warns that the fragment breaks those
rules.

> [!NOTE]
> Rule 2 is what stops one value acquiring three spellings again. Before
> the catalogue existed nothing could have caught it, and the result was
> a field that a descriptor could deny under one name and leak under
> another (§6.4).
