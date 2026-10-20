---
title: The Chooser
description: What a chooser shows and lets the person do — folders as they may see them, and making, renaming and deleting as themselves — and what it must ask before offering.
---

The chooser shows one folder at a time, and lets the person move among
folders. Beyond choosing, it MAY let them make a folder, and rename and
delete files and folders: a small file manager, so that a person saving
a file can make somewhere to put it.

## As the person

The chooser runs as the same person as the requester, started as its
child. Everything it does to files and folders is that person's act,
which KACS checks as for any program of theirs. The chooser MUST NOT
hold or use any authority beyond theirs.

## Asking before offering

The chooser MUST NOT guess what the person may do from who they are.
Before it offers an act, it SHOULD find out whether the person may do
it, by asking the system: an AccessCheck of the person's token against
the descriptor of the folder or the file. What the person may not do it
SHOULD show disabled, with the reason in words, rather than hide it or
offer it to fail. Where the descriptor cannot be read, it MAY offer the
act and let the system decide.

A folder the person may not list MUST be shown as such, with the
reason, and not as an empty folder.

## Deleting

The chooser MUST ask the person before it deletes anything, and say
when a folder will be deleted with everything in it.
