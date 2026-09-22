---
title: Scope and Roles
description: What PGSS Applications specifies and who its parties are — a program declared to a desktop by a file, the directory of such files as the catalogue, and the rules by which a consumer lists, names, starts and opens with an application.
---

This chapter specifies **PGSS Applications**: what a program *is* to a
desktop on a Peios system. Its title, the icon it has, how it is
started, and what kinds of file it opens.

The chapter rests on one decision. An application is a **declaration**,
not a place. A program is not an application because of the directory
it is installed in or the name it is installed under, and a desktop
does not find applications by looking at programs. A package that ships
an application also installs one small file that says what it is, and
the directory of those files is the catalogue (§5.4). Presence is the
catalogue: nothing runs at install, nothing registers, and nothing
indexes.

Two roles participate.

The **provider** declares. A package that installs a program and its
declaration is a provider.

The **consumer** reads the declarations and acts on them. A launcher
that lists what can be started, a dock or taskbar that names a running
program, a file explorer that offers what opens a file, and a
compositor that starts what a launcher picks are all consumers, and a
provider cannot tell them apart.

Both roles are publicly implementable. A third party MAY ship an
application, or a consumer, and interoperate with the rest unchanged. A
consumer that lists, names or starts applications MUST find them as
specified here, precisely so that a provider need say what a program is
once, to everyone.

This chapter covers:

- what a declaration is, where it is, and what it says (§5.3)
- what the catalogue is, and how a consumer reads it (§5.4)
- how a consumer finds the declaration for a program it has met,
  running or on disk, and so the program's title and icon (§5.5)
- how a consumer starts an application, bare or with a file (§5.6)

This chapter does not cover:

- Which application opens a kind of file when several could. §5.6 gives
  a consumer the candidates; choosing among them, and remembering the
  choice, is a later version's.
- Declarations of a person's own, or of a system's local layer, beyond
  what the catalogue's directory admits. This version has one catalogue.
- How a consumer determines a file's type. §5.6 takes the type as given,
  as PGSS Icons §4.6 does.
- What a program does once started, or how a consumer confines it. The
  environment a consumer starts a program in is the consumer's.
- What a program looks like. That is PGSS Icons (§4); this chapter
  gives a program an icon by name, under §4.5, and says nothing about
  pictures.
