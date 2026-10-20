---
title: The Channel
description: The chooser's standard input and output, one JSON object a line; who starts whom; and how either end knows the other has gone.
---

## Starting the chooser

The requester MUST start the chooser as a child process of its own, with
the chooser's standard input and standard output connected to it. It
SHOULD start the chooser with its own environment, which is how the
chooser finds the desktop to draw on, and the person's home folder.

The chooser's standard error is not part of the channel. The chooser MAY
write diagnostics there for an administrator, and the requester MUST
NOT read meaning into them.

## Lines

Each direction is a sequence of lines (§9.2): one compact JSON object,
UTF-8, then a line feed. A line MUST NOT contain a line feed before its
end.

- Requester to chooser, on the chooser's standard input: the request
  (§9.4), first and exactly once, and nothing else in this revision.
- Chooser to requester, on the chooser's standard output: the answer
  (§9.5), at most once, and nothing else in this revision.

The answer carries a `type` member naming what it is. The request is
identified by being first.

A party MUST ignore a line whose `type` it does not recognise, and a
member of an object it does not recognise (§9.7). A party MAY refuse a
line longer than 1 MiB.

## Ending

**The chooser ends** once it has answered, and when the person closes or
cancels the dialog, which it answers as `cancelled` first. It ends by
exiting, which closes its standard output.

**The requester ends**, or gives up on the chooser, by closing the
chooser's standard input. The chooser MUST end promptly when it reads
end-of-file there, without answering and without asking the person
anything: nobody is left to use the answer. A requester that exits
closes the chooser's input whether it means to or not, so the chooser
goes with it. The chooser SHOULD also arrange to be signalled when its
parent exits (on Linux, `PR_SET_PDEATHSIG`), and end then.

A requester that reads end-of-file on the chooser's output with no
answer MUST treat it as `cancelled`. It MUST NOT infer anything from the
chooser's exit status.
