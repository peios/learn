---
title: Extension
description: The skeleton file carries no version number; what may change in it, and what may not without a new path.
---

The skeleton file carries no version number. A provider changes what a
root holds by changing the file's entries, which needs no change to this
chapter.

## What may not be added without a new file

A new kind of entry, such as a regular file or a device node. A new field
on an existing entry. A change to the meaning of an existing shape.

An applier that met such a line would reject the whole file (§11.4).
Such a change therefore needs a new file at a new path, which old
appliers do not read, and which the provider ships beside this one for
as long as old appliers remain.

## What may never be added

**Anything under `/usr`, or anything that removes or changes what a root
holds.** Packages own `/usr`. A skeleton only adds what is missing, so
applying it to a running system or an upgraded root is always safe.
