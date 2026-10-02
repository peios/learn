---
title: The Channel
description: The editor's standard input and output, one JSON object a line; who starts whom; and how either end knows the other has gone.
---

## Starting the editor

The requester MUST start the editor as a child process of its own, with
the editor's standard input and standard output connected to it. It
SHOULD start the editor with its own environment, which is how the
editor finds the desktop to draw on.

The editor's standard error is not part of the channel. The editor MAY
write diagnostics there for an administrator, and the requester MUST
NOT read meaning into them.

## Lines

Each direction is a sequence of lines (§8.2): one compact JSON object,
UTF-8, then a line feed. A line MUST NOT contain a line feed before its
end; compact JSON never needs one.

- Requester to editor, on the editor's standard input: the request
  (§8.4), first and exactly once, then one answer for each `apply`
  (§8.5).
- Editor to requester, on the editor's standard output: `apply`
  messages (§8.5), and nothing else in this revision.

Every line carries a `type` member naming what it is, except the
request, which is identified by being first.

A party MUST ignore a line whose `type` it does not recognise, and a
member of an object it does not recognise (§8.7). A party MAY refuse a
line longer than 1 MiB; a request carrying a descriptor of the largest
size PCDS §5.1 permits is well inside it.

## Ending

The channel ends when either party closes its end, and either party can
tell when the other has.

**The editor ends** when the person closes or cancels the dialog, and
after the person confirms once what it sent has been applied (§8.5). It
ends by exiting, which closes its standard output; the requester reading
end-of-file there is how it knows. An editor that ends sends nothing
more and applies nothing, since it never could.

**The requester ends**, or gives up on the editor, by closing the
editor's standard input. The editor MUST end promptly when it reads
end-of-file there, whatever it is doing, and MUST NOT ask the person
anything first: the requester can no longer apply what they would say.
A requester that exits closes the editor's input whether it means to or
not, so the editor goes with it.

The editor SHOULD also arrange to be signalled when its parent exits
(on Linux, `PR_SET_PDEATHSIG`), and end then. A process whose parent
exits is not ended by that, and an editor left showing a dialog for an
object nobody can apply to is worse than none.

The editor's exit status says nothing about what was applied. The
requester knows that from its own answers (§8.5), and MUST NOT infer it
from the status.
