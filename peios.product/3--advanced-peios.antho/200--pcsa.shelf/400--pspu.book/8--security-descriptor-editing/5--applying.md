---
title: Applying
description: The editor sends the whole descriptor and which components changed, only when the person says to; the requester applies exactly those, and answers once.
---

## `apply`

When the person asks for what they have done to take effect — Apply,
or OK — the editor sends:

| Member | Type | Meaning |
|---|---|---|
| `type` | `"apply"` | |
| `sd` | string | The whole descriptor as the person now has it, self-relative and in base64 as in the request (§8.4). |
| `parts` | array of strings | The components of `sd` that changed since the request, or since the last `apply` the requester answered `applied`: some of `owner`, `group`, `dacl`, `sacl`, `label`. |
| `propagate` | boolean | Optional, `false` when left out. Once `parts` is applied, push what the object now passes down into what is already inside it (see [Pushing into what is inside](#pushing-into-what-is-inside)). |

The editor MUST NOT send an `apply` as the person changes things, only
when they ask for it. A descriptor applied part way through a change
can take away the access the person needs to finish it: denying
Everyone before granting oneself, say.

The editor MUST NOT name `dacl` in `parts` unless the request's
`can.dacl` was true or left out, nor `owner` or `group` unless
`can.owner` was true, nor `sacl` unless `can.audit` was and the request
held the whole SACL, nor `label` unless `can.label` was. It MUST NOT
send `propagate` true unless `can.propagate` was, nor without the
person having chosen it for this `apply`. It MUST NOT send an `apply`
while one is unanswered, and SHOULD NOT send one whose `parts` is
empty. It MAY send one whose `parts` names components that have not
changed since they were applied, with `propagate` true, to push them
into what is inside again (after a walk was stopped or some of it
failed): applying them again changes nothing.

## The label

The label is in the SACL, and `sacl` carries it: a changed label goes
with a changed SACL. `parts` MUST NOT name both `sacl` and `label`,
which KACS refuses to apply together (KACS set-security). `label` names
the label alone, where the rest of the SACL has not changed or cannot
be applied: the SACL of `sd` then holds the label that is to be the
object's, or none to remove it, and the requester applies it as a label
(LABEL_SECURITY_INFORMATION), which keeps the rest of the object's SACL
as it is. A requester that keeps a descriptor whole, as a registry value,
puts the label into the SACL it has, in place of the label there.

## The answer

The requester MUST answer every `apply` with exactly one line, in the
order they came:

| Line | Meaning |
|---|---|
| `{"type":"applied"}` | Every component in `parts` was applied. Where `propagate` was true, it carries how pushing into what is inside went (below). |
| `{"type":"failed","why":"…"}` | None was, or not all, and `why` says why, as text for the person. Nothing was pushed into what is inside. |

The requester MUST apply the components named in `parts`, and MUST NOT
apply any other component of `sd`. The rest is as the requester sent
it, or as the editor could not read it, and writing it back would at
best change nothing and at worst write over what changed meanwhile.

The requester SHOULD apply the named components in one operation where
the kind of object allows it. Where it cannot, and some were applied
and some were not, it MUST answer `failed` and SHOULD say which were
applied.

`why` is shown to the person as it stands. It SHOULD say what was in
the way in words they can act on — "you are not allowed to" — rather
than an error code.

## Pushing into what is inside

Inheritance is eager (PCDS §5.6): what a container passes down reaches
the things made inside it afterwards, and the things already there keep
what they were given. Where the person changes what a container passes
down, the editor SHOULD ask whether to update what is already inside
too, and, where they say yes, sends the `apply` with `propagate` true.

A requester sent `propagate` true first applies `parts` as above. If it
answers `failed`, it pushes nothing. Otherwise, before it answers, it
re-propagates everything inside the object as PCDS §5.6 sets out
(Re-propagation), for the lists `parts` names: the DACL for `dacl`, the
SACL for `sacl`, and for `label` the SACL as far as it holds labels,
read and applied as labels. In particular it MUST:

- go parents first, re-propagating each item from its parent as just
  rewritten;
- leave a list an item protects exactly as it is, and still re-propagate
  what is inside that item from it as it is;
- resolve CREATOR OWNER and CREATOR GROUP against each item's own owner
  and group, and map generic rights through the generic mapping of the
  kind of thing it holds;
- change no component of an item but the lists it re-propagates;
- follow no link out of the tree;
- carry on past an item it cannot read or change, noting it, and leave
  what is inside that item as it is.

The editor sends nothing for the items inside: what each gets is worked
out by the requester, from the object as it now is.

While it walks, the requester MAY send:

| Line | Meaning |
|---|---|
| `{"type":"progress","done":n,"at":"…"}` | `done` items have been re-propagated, the last being `at`, by what the person knows it as. |

It needs no answer. A requester SHOULD send one now and then on a long
walk, and SHOULD NOT send them more often than a person can read.

The editor MAY send, while it waits for the answer to an `apply` with
`propagate` true:

| Line | Meaning |
|---|---|
| `{"type":"stop"}` | Stop the walk after the item in hand. |

It needs no answer of its own: the requester stops, and answers the
`apply` as it would have at the end. What was re-propagated stays so.
End-of-file on the requester's input from the editor means the same.

The `applied` answer to an `apply` with `propagate` true carries:

| Member | Type | Meaning |
|---|---|---|
| `done` | number | How many items inside were re-propagated, those that protect every list included. Left out, none. |
| `failed` | array | The items that could not be, each `{"name":"…","why":"…"}`: what the person knows it as, and why, as text for the person. Left out, none. |
| `stopped` | boolean | Whether the walk was stopped before the end. Left out, it was not. |

Each of these concerns the items inside, not the object: `applied`
still means the object's `parts` were all applied. The editor SHOULD
show how far the walk got, a way to stop it, and afterwards what could
not be done, and SHOULD NOT end on an apply-and-close whose walk failed
for some items or was stopped, so that the person sees it.

## After the answer

On `applied`, the editor takes what it sent as the descriptor it is
editing from then on: a later `apply` names only what changed after.
If the person had asked to apply and close, the editor ends (§8.3).

On `failed`, the editor MUST show the person `why` and MUST NOT end
because of it: what they did is still there to be put right or
abandoned. What it has not had answered `applied` it still counts as
changed.
