---
title: Fields
description: How a field is named — role.thing.attribute for participants, domain.attribute for the event — nesting as the name, value-or-map, the header's names, related things, variants and standard attributes, and who may define a path.
---

A field is named for the part it plays in the event, then for what it
is, then for which property of it the value is:

```text
<role>.<thing>[.<thing>…].<attribute>      subject.token.sid
<domain>[.<…>].<attribute>                 outcome.success
```

## Nesting is the name

A payload is a MessagePack map with string keys. A field's path is the
chain of keys leading to its value: `subject.token.sid` is the value at
`{subject: {token: {sid: …}}}`. An emitter MUST encode a path as nested
maps, one map per segment, and MUST NOT write a key containing `.`; such
a key is a different and unreachable field (PSPU §3.22).

Every segment of a path MUST match the segment grammar of §6.3,
including the segments of a package name that a third party's own
fields sit beneath (below). A package whose name has a segment the
grammar does not admit cannot define fields of its own.

**A path is either a value or a map, never both.** Once any event
carries a value at a path, no field may be defined beneath that path,
and a path defined as a map MUST NOT carry a value in any event. The
shape of a subtree is therefore decided before its first field is
defined, and the variant rule below exists so that it rarely has to be.

## Roles

A path that describes a participant leads with its role. The roles are a
closed set.

| Role | Participant |
|---|---|
| `subject` | Whose authority the action used: the principal that acted |
| `object` | What the action was done to |
| `source` | Where something came from: the origin of a copy, of traffic, of data a backend supplied |
| `destination` | Where it went |
| `emitter` | Who was running when the record was written |

After the role comes the thing, and then the attribute:
`subject.token.sid`, `object.file.path`, `source.stratum.index`.

The emitter and the subject are different participants. The emitter is
whoever wrote the record; the subject is whoever acted. They are the
same on most events, and differ on every event one component writes
about another: an access check a daemon requests for a client has the
daemon as emitter and the client as subject. A consumer searching for
what a principal did MUST search `subject.*`, not `emitter.*`.

## Domains

A path that does not describe a participant leads with a domain, then
the attribute: `outcome.success`, `access.granted`.

A domain names either a property of the event itself, or a thing the
event happened within without acting on it: a ring buffer, a
connection-tracking flow, a transaction. A thing the event acts on is a
participant and takes a role (`object.mount.path`); a thing it happens
within leads with its own name (`buffer.fill`, `flow.state`).

The **generic roots** are shared by every emitter and defined in the
platform fragment (§6.10):

| Root | Holds |
|---|---|
| `subject`, `object`, `source`, `destination`, `emitter` | The participants, and their common things: `token`, `process`, `file`, `key`, `session` |
| `event` | The record's own header values (below) |
| `access` | Rights asked for, granted and audited |
| `outcome` | Whether the action succeeded, and why not (§6.6) |
| `trigger` | Whatever caused the record to exist: an audit ACE, a blocking layer, a causing file |
| `operation` | What was attempted and how |
| `config` | A configuration value reported on |
| `policy` | A rule set in force |
| `transaction` | A transaction an operation belonged to |
| `fields` | Properties of the record's fields (§6.7) |

A platform component MAY define a domain of its own for things only it
has, such as a ring buffer or a service graph, and owns it (§6.10). Any
other emitter's own fields go beneath its package name (below), because
a domain is one segment wide and two vendors' choices would collide.

## The header

The record header (PSPK §2) is stamped by the kernel and cannot be
forged by the emitter. A consumer that exposes header values by name
MUST expose them under these field paths:

| Header field (PSPK §2) | Field path | Type |
|---|---|---|
| `type` | `event.type` | `str` |
| `timestamp` | `event.time` | `uint.time` |
| `sequence` | `event.sequence` | `uint` |
| `cpu_id` | `event.cpu` | `uint` |
| — | `event.boot.guid` | `bin.guid` |
| `origin_class` | `emitter.class` | `uint.enum` |
| `effective_token_guid` | `emitter.token.guid` | `bin.guid` |
| `true_token_guid` | `emitter.true-token.guid` | `bin.guid` |
| `process_guid` | `emitter.process.guid` | `bin.guid` |

`event.boot.guid` is not in the record: it is the boot the consumer read
the record in, which the consumer supplies. `emitter.class` is a
`uint.enum` whose numbers are PSPK §2's origin classes, which is why it
is not a string (§6.5).

An emitter MUST NOT write any of these paths in a payload. Details of
the emitting process that the header does not carry — its PID, name and
executable — are payload fields under `emitter.process`.

## Things and their relations

A thing related to a participant nests under it: the parent of a process
is `object.process.parent.pid`, the target of a registry symlink is
`object.key.target.guid`, the token a job runs as is
`object.job.token.sid`.

Two things of one kind that appear in one event are told apart by
direction where there is one: `source` and `destination`. Where there is
no direction, the second is named by its relation to the first, as
above. A path MUST NOT use `other`, `peer` or a similar segment to tell
two participants apart.

`key` as a thing means a registry key and nothing else. A cryptographic
key is a `signing-key`, a handle is a `handle`.

`capability` as a thing or attribute means a confinement capability SID.
A Linux capability is `linux.cap`, which is context for a privilege
decision and never the decision itself.

## Many values

Many values of one field go in an array under a plural name:
`subject.token.groups`. Arrays that describe the same items are
parallel and share an index: `subject.token.group-attributes[i]`
describes `subject.token.groups[i]`.

## Variants

A variant of a value is a sibling of it, named with a qualifier suffix,
and the plain name always holds the value in force:

| Path | Value |
|---|---|
| `policy.generation` | The generation now in force |
| `policy.generation-previous` | The generation it replaced |
| `object.key.path` | The key's resolved path |
| `object.key.path-requested` | The path as the caller wrote it |

A qualifier MAY also sit on a thing, where the variant is a whole
thing: `source.stratum-previous.path`.

The following qualifiers MAY be applied to any defined field or thing
without that variant being defined separately: `-previous`,
`-requested`, `-expected`, `-effective`, `-limit` and `-count`. This set
is closed in this version. Any other qualifier is part of a field's
name, and the field MUST be defined like any other (§6.10).

> [!NOTE]
> Variants are siblings rather than children because of the
> value-or-map rule. If before and after were last segments,
> `policy.generation.previous` could not exist beside a
> `policy.generation` that other events already carry as a value. A
> sibling also sorts next to the value it qualifies.

## Standard attributes

These attributes MAY be attached to any defined thing or domain without
being defined separately: `count`, `limit`, `length`, `size`, `depth`,
`capacity`, `fill`, `duration`, `timeout`, `attempts`, `offset`,
`index`, `sequence`, `generation`, `digest`, `name`, `path`, `id`,
`guid`, `sid`, `type` and `state`. Each has the type its name implies in
§6.5. This set is closed in this version.

## Who may define a path

Every path is defined exactly once across the catalogue (§6.10).

The generic roots of the table above, and their common fields, are
defined in the platform fragment. A component defines the subtrees of
things only it knows about — StrataFS defines `source.stratum.*` — and
any domain of its own. Any emitter MAY carry a field defined by another
fragment without defining it.

A field that no generic path or platform subtree covers, and that an
emitter that is not a platform component needs, sits beneath its own
package name below the role:
`object.org.jellyfin.server.media.title`. Such a field SHOULD be rare,
and an emitter SHOULD use a defined field wherever one has the meaning
it needs.

An emitter MUST NOT write a field that the catalogue does not define,
other than a variant or standard attribute permitted above.

## Names are access control

A consumer that controls read access per field treats each path as an
object in an access check (PSPU §3.28). Because the path is nested, a
grant on `subject` can cover every identity field beneath it, including
fields defined later. Because each value has one path, a descriptor that
denies a value cannot be evaded by writing the value under a second
name. That is the security reason for the one-definition rule, and why
the catalogue rejects a duplicate (§6.10).
