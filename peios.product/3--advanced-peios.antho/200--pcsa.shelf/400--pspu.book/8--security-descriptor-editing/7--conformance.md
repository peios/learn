---
title: Conformance
description: Every requirement of this chapter collected by role — the requester and the editor.
---

## A conforming requester

**Starting.** Starts the editor as its own child with the editor's
standard input and output connected to it, and sends the request as the
first line (§8.3).

**The request.** Sends every required member, a self-relative
descriptor in padded base64, the general rights from the most to the
least, and the generic mapping its kind of object actually uses. Says
in `can` only what it can in fact change (§8.4).

**Applying.** Answers every `apply` with exactly one line, in order.
Applies the components `parts` names and no others. Answers `applied`
only when all of them were, and otherwise `failed`, with a reason for
the person (§8.5).

**Lines.** Ignores a line type and a member it does not recognise
(§8.3). Infers nothing from the editor's exit status or standard error
(§8.3).

## A conforming editor

**Starting.** Shows no dialog for a request it cannot use, and ends
(§8.4).

**Showing.** Shows a descriptor without a DACL as granting everyone
everything, never as an empty list. Shows what it cannot express in the
general rights as a whole, and keeps such entries as it found them
(§8.4).

**Applying.** Sends an `apply` only when the person asks, with the
whole descriptor and the components that changed, never `owner` or
`sacl` it was not told it could, and never while one is unanswered.
Shows a `failed` answer's reason and stays (§8.5).

**Changing nothing.** Holds no handle to the object and changes nothing
itself (§8.1, §8.6).

**Ending.** Ends when the person closes or cancels, after an `applied`
answer to an apply-and-close, and promptly on end-of-file on its
standard input, without asking the person anything. SHOULD also end
when its parent exits (§8.3).
