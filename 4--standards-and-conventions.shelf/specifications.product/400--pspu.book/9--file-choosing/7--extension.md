---
title: Extension
description: The choosing channel carries no version number; what may be added to it, what may not without a new revision, the revisions so far, and the one thing that may never be.
---

The choosing channel carries no version number. It grows by addition,
under these rules.

## What may be added

A **member** of the request or of the answer. A party MUST ignore a
member it does not recognize, so a requester MAY send one and MUST NOT
depend on its effect.

A **line type** from the chooser that the requester may ignore and
still conform: a requester MUST ignore a `type` it does not recognize
(§9.3), and goes on waiting for the answer.

## What may not be added without a new revision

A change to the meaning of an existing member or line. A `mode` beyond
those of the current revision. A second answer, or a line from the
requester after the request.

## Revisions

**Revision 1** defined the `open` and `save` modes.

**Revision 2** adds the `folder` mode (§9.4, §9.5). It adds no member
and changes nothing in revision 1. A revision-1 chooser receiving a
`folder` request cannot use it: it shows no dialog and ends without
answering (§9.4), which the requester treats as `cancelled` (§9.3).
Nothing is chosen, and no folder reaches a requester that cannot handle
one. A requester that asks for a folder MUST be prepared for that
outcome as for any `cancelled`.

## What may never be added

**A way for the chooser to hand over a file.** Nothing on the channel
may carry an open file, its contents, or anything but a path from the
chooser to the requester. The requester opening what it is pointed at,
as the person, is what lets any program use a chooser it does not
trust.
