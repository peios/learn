---
title: The Request
description: The first line the requester sends — the object, its descriptor, what its rights are called, what its generic rights mean, and which components it can change.
---

The request is the first line on the editor's standard input, and the
only one that has no `type`. It is one JSON object:

| Member | Type | Required | Meaning |
|---|---|---|---|
| `object` | object | Yes | What the descriptor is the descriptor of. |
| `object.name` | string | Yes | What the object is called where the person found it: `notes.txt`, not a full path, unless a path is how they know it. |
| `object.kind` | string | Yes | What kind of thing it is, in words for the person: `File`, `Folder`, `Service`. |
| `object.container` | boolean | No, `false` | Whether other objects inherit from it (PCDS §5.6). |
| `object.children` | string | No, `"all"` | What a container holds, which is what the entries made for it are passed on to: `all` or `containers` (see [Containers](#containers)). Ignored unless `container` is true. |
| `object.parent` | object | No | What the object is in, which its inherited entries come from (see [The parent](#the-parent)). |
| `object.parent.name` | string | Yes, in `parent` | What the parent is called where the person knows it: `/srv`. |
| `object.parent.sd` | string | No | The parent's descriptor, self-relative and in base64 as `sd` is. |
| `object.parts` | array | No, empty | The object's parts that rules can be made for one at a time: object types (see [Parts and kinds](#parts-and-kinds)). |
| `object.parts[].guid` | string | Yes | The object type, as a GUID in its usual text form: `bf967aba-0de6-11d0-a285-00aa003049e2`. |
| `object.parts[].name` | string | Yes | What the part is called, for the person. |
| `object.parts[].kind` | string | Yes | `set`, a set of properties; `property`; or `right`, an action. |
| `object.parts[].set` | string | No | For a property, the GUID of the set it is in. |
| `object.kinds` | array | No, empty | On a container of typed things, the kinds of thing it holds: inherited object types. |
| `object.kinds[].guid`, `.name` | string | Yes | The inherited object type, and what that kind of thing is called. |
| `object.part_rights` | array | No, empty | The rights a rule for a part can give, as `rights` gives the object's (see [Parts and kinds](#parts-and-kinds)). |
| `object.part_rights[].name`, `.mask` | string, number | Yes | What the right is called, and its access mask. |
| `object.naming` | object | No | How a part not listed is named (see [Parts named by the person](#parts-named-by-the-person)). |
| `object.naming.namespace` | string | Yes, in `naming` | The UUID v5 namespace a part's object type is derived in, as a GUID in its usual text form. |
| `object.naming.noun` | string | Yes, in `naming` | What one such part is called, for the person: `field`. |
| `object.naming.example` | string | No | A name the person might give, to show how one is written: `source.name`. |
| `sd` | string | Yes | The descriptor as it is now: a self-relative Security Descriptor (PCDS §5.1), in base64 with padding (RFC 4648 §4). |
| `read` | array of strings | No | The components `sd` holds as they are on the object: some of `owner`, `group`, `dacl`, `sacl` and `label` (see [The descriptor](#the-descriptor)). Left out, every component `sd` has. |
| `rights` | array | Yes | The object's rights by name, in the order a person should see them. |
| `rights[].name` | string | Yes | What the right is called. |
| `rights[].mask` | number | Yes | The access mask the right stands for, as an unsigned 32-bit integer. |
| `rights[].general` | boolean | No, `false` | Whether it is a general right (§8.2). |
| `generic` | object | Yes | What each generic right stands for on this kind of object (PCDS §5.3). |
| `generic.read`, `.write`, `.execute`, `.all` | number | Yes | The access mask each generic right maps to. |
| `can` | object | No | Which components the requester is able to change. |
| `can.dacl` | boolean | No, `true` | Whether it can change the DACL. It is true when left out because, before this member, a requester always could. |
| `can.owner` | boolean | No, `false` | Whether it can change the owner. |
| `can.audit` | boolean | No, `false` | Whether it can change the SACL. |
| `can.label` | boolean | No, `false` | Whether it can apply the label by itself (§8.5). |
| `can.propagate` | boolean | No, `false` | Whether, on a container, it can push what was applied into what is already inside (§8.5, Pushing into what is inside). |
| `can.why` | string | No | Why the requester cannot change what `can` says it cannot, as text for the person. |

## The descriptor

The requester SHOULD include the owner, the group and the DACL. It MAY
leave out the SACL: reading a SACL takes ACCESS_SYSTEM_SECURITY, which
a requester need not have. It SHOULD include the label where it can
read it, which takes only READ_CONTROL. A requester that could read the
label and not the rest of the SACL sends a SACL holding the label
alone, and MUST then say so in `read`, naming `label` and not `sacl`.

The editor MUST NOT take a SACL for the whole SACL unless `read` names
`sacl` or is left out. Where it is only the label, the editor MUST NOT
show it as an object with no auditing, claims or policies, since those
are not known.

A descriptor with no DACL component means one with no access list,
which PCDS §5.1 treats as granting everyone everything. The editor MUST
show it as such and not as an empty list, which grants nobody anything.

## The parent

`object.parent` names what the object's inherited entries come from,
for the person: "Inherited from /srv". An editor that offers to stop
inheriting MAY offer to inherit again, but KACS does not pass a
parent's entries down again by itself when protection is turned off
(PCDS §5.6): the editor works out what is passed down from
`object.parent.sd`, and SHOULD NOT offer to inherit again without it.
A requester SHOULD send the parent's descriptor where it can read it.

## Parts and kinds

`object.parts` lists the object types (PCDS §5.4) a rule can be made
for, as an account's sign-in details or the action of resetting its
password. `object.kinds` lists, for a container of typed things, the
kinds of thing it holds, which an entry can be passed on to alone. An
editor MAY offer rules for parts and kinds only where they are listed,
and MUST keep as it found it an entry naming a GUID it is not told of.

`object.part_rights` names what a rule for a part can give. Left out,
an editor offers what a directory's parts take: reading and writing a
property, and using an action. A requester whose parts take other rights
MUST send them. eventd's fields, for example, take only its Read.

### Parts named by the person

Some objects have more parts than can be listed, each one's object type
derived from its name. eventd's fields are an example: a payload field
needs no registration, and its GUID is derived from its name (eventd TRM
§7.3). `object.naming` tells the editor how such a part is named. Its
object type is the UUID v5 (RFC 9562 §5.5) of the name, as UTF-8, in
`naming.namespace`, and it is a property.

An editor MAY then let the person name a part beside those listed. It
MUST derive the object type exactly so, and SHOULD show the part by the
name given for as long as the dialog is open. A requester SHOULD still
list in `parts` the ones it knows, so that an existing rule for one is
shown by name.

## The rights

`rights` names every right the requester wants a person to see.
General rights SHOULD come first, from the one granting the most to the
one granting the least, so that a right that includes another is above
it. The masks of two rights MAY overlap, and typically do: "Modify"
includes "Read".

An editor that shows general rights as boxes to tick SHOULD show as a
whole what a mask it cannot express in them — a mask with bits outside
every general right it contains, an entry of a type it does not edit,
or inheritance flags other than its own — rather than leave it unshown,
and SHOULD keep such an entry as it found it.

`generic` lets the editor read an entry that grants generic rights
(PCDS §5.3) as the rights they stand for. The requester MUST give the
mapping its kind of object actually uses.

## Containers

On a container, the entries an editor makes apply to the container and
are passed on to what it holds. `object.children` says what that is,
and so which inheritance flags (PCDS §5.6) those entries carry:

| Value | Holds | Flags of an entry made here |
|---|---|---|
| `all` | Containers and other objects, as a folder holds folders and files. | Object inherit and container inherit. |
| `containers` | Containers alone, as a registry key holds keys and nothing else. | Container inherit. |

An entry with other inheritance flags is one the editor cannot express
in its general rights (above), and is shown as a whole and kept.

## What the requester can change

`can` says what the requester is able to change. It MUST NOT say it
can change a component it cannot. `can.label` is true only where it can
apply the label by itself, which takes WRITE_OWNER and, for a level
above the caller's own, SeRelabelPrivilege (KACS set-security). It SHOULD find out by asking the
system, for example by an AccessCheck of the person's token against the
descriptor, or by opening the object for the rights that changing it
takes. It SHOULD NOT infer it from the person's group memberships.

`can.propagate` is true only on a container whose requester holds what
is inside it and can walk it: a file explorer for a folder, a registry
editor for a key. It says nothing about whether each item inside can be
changed, which is found out item by item as the walk goes (§8.5).

A requester that cannot change the DACL still sends it, so that the
person can read it. The editor MUST then show the DACL without offering
to change it, and SHOULD say why, with `can.why` if it was given. An
editor whose requester can change nothing SHOULD offer only to close.

## Validation

An editor that cannot use the request — one that is not a JSON object,
lacks a required member, or carries an `sd` that is not a Security
Descriptor — MUST NOT show a dialog. It SHOULD write why to its
standard error, and MUST end (§8.3).
