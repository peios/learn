---
title: Terminology
description: Terms this chapter defines for itself — requester, chooser, line, request, answer, mode, filter.
---

**Requester.** The program that wants a file chosen, and which started
the chooser. §9.1

**Chooser.** The program that shows the person's folders and answers
with the file they choose. §9.1

**Line.** One message on the choosing channel: a single compact JSON
object, encoded as UTF-8, followed by a line feed (U+000A). §9.3

**Request.** The first line the requester sends: everything the chooser
is told about what is wanted. §9.4

**Answer.** The one line the chooser sends: the path chosen, or that
nothing was. §9.5

**Mode.** Whether an existing file is to be opened (`open`) or a place
and a name to be saved to (`save`). §9.4

**Filter.** A kind of file the requester offers, named for the person
and given as a list of extensions. §9.4
