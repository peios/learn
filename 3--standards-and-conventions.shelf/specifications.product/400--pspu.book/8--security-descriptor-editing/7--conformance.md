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
least, and the generic mapping its kind of object actually uses. On a
container, says in `object.children` what it holds. Says in `can` only
what it can in fact change, having asked the system. Says in `read`
which components it sent where that is not everything `sd` has, as a
SACL holding only the label (§8.4).

**Applying.** Answers every `apply` with exactly one line, in order.
Applies the components `parts` names and no others, and the label as a
label, keeping the rest of the SACL. Answers `applied` only when all of
them were, and otherwise `failed`, with a reason for the person (§8.5).

**Pushing into what is inside.** Says `can.propagate` only on a
container it can walk. Asked to, after applying, re-propagates
everything inside as PCDS §5.6 sets out, for the lists `parts` names:
parents first, protected lists left, nothing changed but those lists, no
link followed, past an item it cannot change. Stops after the item in
hand on `stop` or end-of-file, and answers `applied` with how many were
done, which could not be and why, and whether it was stopped (§8.5).

**Lines.** Ignores a line type and a member it does not recognise
(§8.3). Infers nothing from the editor's exit status or standard error
(§8.3).

## A conforming editor

**Starting.** Shows no dialog for a request it cannot use, and ends
(§8.4).

**Showing.** Shows a descriptor without a DACL as granting everyone
everything, never as an empty list. Shows what it cannot express in the
general rights as a whole, and keeps such entries as it found them.
Gives the entries it makes on a container the inheritance flags of what
the container holds. Shows a DACL the requester cannot change without
offering to change it. Takes a SACL for the whole SACL only where
`read` says it is (§8.4).

**Applying.** Sends an `apply` only when the person asks, with the
whole descriptor and the components that changed, never `dacl`,
`owner`, `group`, `sacl` or `label` it was not told it could, never
`sacl` and `label` together, and never while one is unanswered.
Shows a `failed` answer's reason and stays (§8.5). Sends `propagate`
only to a requester that said `can.propagate`, and only where the person
chose it (§8.5).

**Changing nothing.** Holds no handle to the object and changes nothing
itself (§8.1, §8.6).

**Ending.** Ends when the person closes or cancels, after an `applied`
answer to an apply-and-close, and promptly on end-of-file on its
standard input, without asking the person anything. SHOULD also end
when its parent exits (§8.3).
