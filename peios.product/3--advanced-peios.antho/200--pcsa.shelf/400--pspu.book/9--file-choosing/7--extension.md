---
title: Extension
description: The choosing channel carries no version number; what may be added to it, what may not without one, and the one thing that may never be.
---

The choosing channel carries no version number. It grows by addition,
under these rules.

## What may be added

A **member** of the request or of the answer. A party MUST ignore a
member it does not recognise, so a requester MAY send one and MUST NOT
depend on its effect.

A **line type** from the chooser that the requester may ignore and
still conform: a requester MUST ignore a `type` it does not recognise
(§9.3), and goes on waiting for the answer.

## What may not be added without a version

A change to the meaning of an existing member or line. A `mode` beyond
`open` and `save`. A second answer, or a line from the requester after
the request.

## What may never be added

**A way for the chooser to hand over a file.** Nothing on the channel
may carry an open file, its contents, or anything but a path from the
chooser to the requester. The requester opening what it is pointed at,
as the person, is what lets any program use a chooser it does not
trust.
