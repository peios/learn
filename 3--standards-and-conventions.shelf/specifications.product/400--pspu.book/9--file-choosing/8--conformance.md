---
title: Conformance
description: Every requirement of this chapter collected by role — the requester and the chooser.
---

## A conforming requester

**Starting.** Starts the chooser as its own child with the chooser's
standard input and output connected to it, and sends the request as the
first line (§9.3).

**The request.** Sends `mode` and `title`, a `folder` that is absolute
if any, and filters with extensions without the dot (§9.4).

**The answer.** Uses a `chosen` path as the person, opening the file
itself, and handles its having gone or the act being refused. Treats
end-of-file without an answer as `cancelled` (§9.3, §9.5). Infers
nothing from the chooser's exit status or standard error, and does not
rely on the person choosing a file of a kind offered (§9.4).

**Lines.** Ignores a line type and a member it does not recognise (§9.3).

## A conforming chooser

**Starting.** Shows no dialog for a request it cannot use, and ends
(§9.4). Starts in the folder given, or the person's home (§9.4).

**Choosing.** Offers the filters in order, the first chosen (§9.4). In
`save` mode, asks before answering with a file that exists (§9.5).
Never opens, creates or changes the chosen file to choose it (§9.5).

**The answer.** Sends at most one, a `chosen` with an absolute path or a
`cancelled`, and ends. Answers `cancelled` when the person closes or
cancels the dialog (§9.3, §9.5).

**Ending.** Ends promptly, without answering or asking, when its
standard input closes (§9.3).

**As the person.** Acts on files and folders only as the person, and
holds nothing beyond their authority. Asks the system what they may do
before offering it, and shows what they may not, with the reason. Shows
a folder they may not list as such. Asks before deleting (§9.6).

**Lines.** Ignores a member it does not recognise (§9.3).
