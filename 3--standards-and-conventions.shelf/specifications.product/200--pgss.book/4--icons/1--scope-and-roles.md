---
title: Scope and Roles
description: What PGSS Icons specifies and who its parties are — an icon as a name, themes as the directories that give a name a picture, and the rules by which any file is given a name.
---

This chapter specifies **PGSS Icons**: how a program, a file, a
directory or a kind of thing on a Peios system is given an icon, and
where the icon comes from.

The chapter rests on one decision. An icon is a **name**, not a picture.
Every party that has something to say about what a thing looks like says
a name, and a name becomes a picture in one place only: the theme chain
(§4.4). A program carries its name in its own file; a file's owner may
set one on it; a file's own name and its type each yield one. Whoever
draws the thing looks the name up, and a theme that provides the same
name decides how it is drawn.

Two roles participate.

The **provider** puts icons where they can be found, and says which one
a thing has. A package that installs an icon into a theme is a provider.
So is a program that carries the name of its icon, and so is a person
who sets a name on a file they own.

The **consumer** draws. Given a thing, it finds the name by the rules of
§4.5 and the picture by the rules of §4.4, and draws what it finds. A
launcher, a taskbar, a file explorer and a compositor drawing window
frames are all consumers, and a provider cannot tell them apart.

Both roles are publicly implementable. A third party MAY ship a theme, a
program carrying an icon, or a consumer, and interoperate with the rest
unchanged. A consumer that draws icons for things it did not make MUST
find them as specified here, precisely so that a provider need say what
a thing looks like once, to everyone.

This chapter covers:

- what a name is, and which names mean what (§4.3)
- what a theme is, where themes are, and how a name becomes a file
  (§4.4)
- how a consumer finds the name for a file: the sources it consults and
  the order it consults them in (§4.5)
- how a file's type yields a name (§4.6)
- the names every system has (§4.A)

This chapter does not cover:

- What a program *is* to a desktop: its title, what it opens, how it is
  started. That is PGSS Applications (§5), which gives a program an
  icon by name under §4.5.
- How a consumer determines a file's type. §4.6 takes the type as
  given.
- How a consumer draws a picture, at what size, or in what colour.
  Rendering is the consumer's.
- Pictures that are not icons: a thumbnail of a photograph, a preview of
  a document. A consumer that shows those shows them instead of an icon,
  by rules of its own.
