---
title: Terminology
description: Terms this chapter defines for itself — requester, editor, line, request, component, general right — and the ones it takes from PCDS.
---

Security Descriptor, access mask, ACE, DACL, SACL, owner, group, and
generic right are used with PCDS §5's meanings and are not redefined.

**Requester.** The program whose object's descriptor is being edited,
and which started the editor. §8.1

**Editor.** The program that shows the descriptor to a person and
sends back what they apply. §8.1

**Line.** One message on the editing channel: a single compact JSON
object, encoded as UTF-8, followed by a line feed (U+000A). §8.3

**Request.** The first line the requester sends: everything the editor
is told about the object. §8.4

**Component.** One of the five separately applicable parts of a
Security Descriptor: the owner, the group, the DACL, the SACL and the
label. The label is the SACL's mandatory integrity label alone, which
KACS applies apart from the rest of the SACL and with a different right
(KACS set-security). On the channel they are named `owner`, `group`,
`dacl`, `sacl` and `label`.

**General right.** A right the requester names for a person to grant
or deny in one step, such as "Read" or "Full control", standing for an
access mask that may have many bits. The requester decides which rights
are general and what each stands for. §8.4

**Applying.** The requester writing components of a descriptor the
editor sent onto the object. §8.5
