---
title: The Answer
description: The one line the chooser sends — the path chosen, or that nothing was — and what a path in each mode promises.
---

The chooser sends at most one answer, and ends after sending it.

| Line | Meaning |
|---|---|
| `{"type":"chosen","path":…}` | The person chose the file, or in `folder` mode the folder, at `path`, an absolute path |
| `{"type":"cancelled"}` | The person chose nothing: they canceled or closed the dialog |

## What a path promises

In `open` mode, the path names a file that existed when the person chose
it. The requester opens it, and MUST handle its having gone, or changed,
since.

In `save` mode, the path names a place the person chose to write to, in
a folder that existed when they chose it. If a file was there, the
person has already said to save over it: the chooser MUST ask before it
answers with the path of a file that exists. The requester creates or
replaces the file, and MUST handle being refused, since what the person
may do can change, and the chooser could not open the file to find out.

In `folder` mode, the path names a folder that existed when the person
chose it: the folder they picked or, with none picked, the folder shown.
The chooser MUST make clear which folder choosing will answer with
before the person chooses, and MUST NOT answer with a path that is not a
folder. The requester MUST handle the folder's having gone, or what it
can do there having changed, since.

Only in `folder` mode does the chooser answer with a folder. In `open`
and `save` modes, choosing a folder MUST go into it rather than answer
with it, so that a requester that asked for a file is never handed a
folder.

The chooser MUST NOT open, create or change the chosen file to choose
it, and MUST NOT answer with a path it has not shown or the person has
not typed. In neither mode does a path grant anything: the requester
uses it as the person, with its own token.
