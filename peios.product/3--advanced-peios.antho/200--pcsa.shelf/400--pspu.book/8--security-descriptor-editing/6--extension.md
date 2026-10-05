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

## What may never be added

**A way for the editor to apply.** Nothing on the channel may let the
editor change the object itself, or ask the requester to apply anything
but a descriptor the person asked to apply. That the editor holds
nothing and is trusted with nothing is what lets a requester open it on
any object, and the requester applying exactly what it is sent is the
whole of the contract between them.
