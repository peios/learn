---
title: Conformance
description: The obligations of each role, gathered in one place.
---

## A conforming consumer

- Reads declarations from `/usr/share/apps/` and no subdirectory of
  it, from files named `<id>.toml` with the id in the form of §5.3, and
  passes over any other file (§5.4).
- Requires nothing of a provider beyond the file's presence (§5.4).
- Reads a declaration by the rules of §5.3: takes the keys it knows,
  ignores the rest, treats an unusable declaration as none and goes on,
  and sets an odd one right as §5.3 says.
- Checks an id's form before making it a path (§5.4).
- Notices a change to the catalogue, or documents how stale a
  remembered read may be (§5.4).
- Matches a program to a declaration by file, never by name, and
  through the process for a running one (§5.5).
- Yields the declaration's `icon` as the identifier for the program
  under PGSS Icons §4.5, and goes on to §4.5's other sources when the
  chain does not provide it (§5.5).
- Starts an application by executing its program with its arguments as
  given, without a shell, splitting, quoting, expansion or path lookup,
  and with a file's path last (§5.6).
- Takes the program and arguments from the catalogue, never from a
  request that names an id (§5.6).
- When it picks among the candidates, picks the default where the type
  has one, and offers it first, or shows which it is, when it offers
  them (§5.6).
- Finds the default from the person's choices and then the machine's,
  each for the exact type and then for its top-level type and `*`, and
  passes over a choice that is malformed or not usable without treating
  it as an error (§5.7).
- Reads the person's choices as the person the file is opened for, and
  never through a `CurrentUser\` of its own on their behalf (§5.7).
- Opens a file with nothing that is not a candidate for it, whatever a
  choice says, and reads a default from nowhere but §5.7's keys (§5.6,
  §5.7).
- When it offers to set choices, finds out whether it may by asking
  the registry, never by the person's groups (§5.7).
- Infers nothing about a program from a match beyond what the
  declaration says (§5.5).

## A conforming provider

- Installs a declaration as `/usr/share/apps/<id>.toml`, with the id in
  the form of §5.3 and within a domain it owns.
- Writes a TOML 1.0 document with a one-line `title` and an absolute
  `program`, and relies on no key outside the table of §5.3.
- Does not rely on any order of listing, on any consumer's reading a
  key it does not know, or on any placeholder in `arguments` (§5.3,
  §5.6).
- Does not declare one program twice (§5.5).

## A conforming system

- Has the catalogue at `/usr/share/apps/`, readable by anyone who can
  log on to a desktop (§5.4).
- Lets anyone who can log on to a desktop read
  `Machine\Generic\Applications\Defaults` where it is present, and
  SHOULD let only administrators write it (§5.7).

## What conformance does not require

Conformance does not require a consumer to list applications in any
order, to show a description, to let a person add arguments, to cache
anything, to determine any file's type, or to offer to set choices. It does not require a
provider to declare every program it installs: a program with no
declaration is a program, and is still drawn and run as one.
