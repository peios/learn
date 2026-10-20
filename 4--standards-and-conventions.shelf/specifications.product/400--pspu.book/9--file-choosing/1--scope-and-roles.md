---
title: Scope and Roles
description: The interface by which a program has a person choose a file to open, or a place and a name to save to, in a dialog that is a program of its own and never opens the file.
---

This chapter defines the **choosing channel**: the interface by which a
program has a person choose a file, either an existing one to read or a
place and a name to write to, in a dialog drawn by another program, the
**chooser**.

The chooser knows nothing of what the file is for. It is told what to
call the dialog, what the file is for in words, where to start, and what
kinds of file to offer. What it answers with is a path, or that the
person chose nothing.

## Roles

**The requester** is the program that wants a file. It starts the
chooser, says what it wants, and, given a path, opens, reads, creates or
writes the file itself.

**The chooser** shows the person's folders and lets them pick a file or
type a name, and answers with the path. It runs as the same person as
the requester, and, as a small file manager, lets them make a folder and
rename and delete as themselves. It never opens the chosen file, and
hands the requester nothing but a path.

The split mirrors §8's. The party that will use the file is the one that
opens it, with its own token, so the chooser is trusted with nothing it
could misuse, and serves any requester without knowing what files are
for.

## What this chapter leaves to others

How the chooser draws its dialog, and on which desktop, is the chooser's
own design and that desktop's. On a GXWI desktop the chooser is an app
like any other, found by the environment it inherits from the requester.

What the person may do with files and folders is KACS's to decide, as it
is for any program of theirs. This chapter says only that the chooser
asks the system rather than guessing (§9.6).

What a requester does with the file, and in what format, is its own
concern.
