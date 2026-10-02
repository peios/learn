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
| `sd` | string | Yes | The descriptor as it is now: a self-relative Security Descriptor (PCDS §5.1), in base64 with padding (RFC 4648 §4). |
| `rights` | array | Yes | The object's rights by name, in the order a person should see them. |
| `rights[].name` | string | Yes | What the right is called. |
| `rights[].mask` | number | Yes | The access mask the right stands for, as an unsigned 32-bit integer. |
| `rights[].general` | boolean | No, `false` | Whether it is a general right (§8.2). |
| `generic` | object | Yes | What each generic right stands for on this kind of object (PCDS §5.3). |
| `generic.read`, `.write`, `.execute`, `.all` | number | Yes | The access mask each generic right maps to. |
| `can` | object | No | Which components besides the DACL the requester is able to change. |
| `can.owner` | boolean | No, `false` | Whether it can change the owner. |
| `can.audit` | boolean | No, `false` | Whether it can change the SACL. |

## The descriptor

The requester SHOULD include the owner, the group and the DACL. It MAY
leave out the SACL, and SHOULD unless `can.audit` is true: reading a
SACL takes a privilege a requester need not have.

A descriptor with no DACL component means one with no access list,
which PCDS §5.1 treats as granting everyone everything. The editor MUST
show it as such and not as an empty list, which grants nobody anything.

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

## Validation

An editor that cannot use the request — one that is not a JSON object,
lacks a required member, or carries an `sd` that is not a Security
Descriptor — MUST NOT show a dialog. It SHOULD write why to its
standard error, and MUST end (§8.3).
