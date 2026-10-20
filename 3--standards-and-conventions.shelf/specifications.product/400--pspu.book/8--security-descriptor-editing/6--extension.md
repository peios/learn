---
title: Extension
description: The editing channel carries no version number; what may be added to it, what may not without one, and the one thing that may never be.
---

The editing channel carries no version number. It grows by addition,
under these rules.

## What may be added

A **member** of the request, or of any line. A party MUST ignore a
member it does not recognise, so a requester MAY send one and MUST NOT
depend on its effect.

A **line type**, in either direction, that the other party may ignore
and still conform: a party MUST ignore a `type` it does not recognise
(§8.3). A line that needs an answer MUST NOT be added this way, since
an editor waiting on an answer from a requester that ignored the
question would wait for ever.

## What may not be added without a version

A change to the meaning of an existing member or line. A component name
beyond the five of §8.2. An answer to `apply` other than the two of
§8.5.

The fifth, `label`, was added without a version because nothing can
send it to a requester that does not know it: an editor names it only
for a requester that said `can.label`, which an older requester never
says.

Pushing into what is inside was added the same way. An editor sends
`propagate` only to a requester that said `can.propagate`. `progress`
and `stop` are lines that need no answer. What `applied` carries about
the walk is members of it, and `applied` still means only that the
object's `parts` were applied.

`object.part_rights` and `object.naming` were added as optional members
of the request. An editor that does not know `naming` offers only the
parts listed. An editor that does not know `part_rights` offers a
directory's rights for a part, which may not be rights the object's
parts take. For eventd's fields they aren't, so such a rule gives
nothing.

`raise` (§8.3) was added as a line that needs no answer. An older
editor ignores it, and its dialog stays where it is.

## What may never be added

**A way for the editor to apply.** Nothing on the channel may let the
editor change the object itself, or ask the requester to apply anything
but a descriptor the person asked to apply. That the editor holds
nothing and is trusted with nothing is what lets a requester open it on
any object, and the requester applying exactly what it is sent is the
whole of the contract between them.

Pushing into what is inside keeps to this. The editor sends no
descriptor for anything but the object, and `propagate` asks only for
what PCDS §5.6 says re-propagation of the object's descriptor is, which
the requester works out itself from the object as it applied it. The
editor cannot choose what any item inside gets.
