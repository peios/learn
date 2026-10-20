---
title: Conformance
description: The obligations of each role, gathered in one place.
---

## A conforming consumer

- Treats as an identifier only a string in the form of §4.3, and looks
  up nothing else.
- Looks in the themes of the chain in order, in `/usr/share/icons/` and
  in no subdirectory of a theme, for `<identifier>.svg`, and takes the
  first (§4.4).
- Reads the chain from `Machine\Generic\Icons` `Themes`, appends the
  base theme, and ignores the base theme anywhere else in the value
  (§4.4).
- Draws an SVG as an image and runs nothing in it (§4.4).
- Notices a change to a theme or the chain, or documents how stale a
  remembered lookup may be (§4.4).
- For a path, consults a governing specification, then
  `user.pgss.icon`, then `.pgss.icon`, then the name, then the type, in
  that order, and draws the first identifier the chain provides, or
  `generic` (§4.5).
- Finds `.pgss.icon` by the section header table, without executing or
  loading the object, and within bounds (§4.5).
- Derives the name source's identifier by lowercase ASCII conversion
  and prefix alone, and special-cases no name (§4.5).
- Yields from a type the whole type and then the top-level type, and
  determines at least a directory and an executable (§4.6).
- Infers nothing about a subject from its icon (§4.5).

## A conforming provider

- Installs a theme as a flat directory of `<identifier>.svg` under
  `/usr/share/icons/<theme>/`, with the theme's name in the form of an
  identifier (§4.4).
- Uses a meaningful form of identifier for its meaning and no other,
  and a reverse-DNS name for a program's own icon (§4.3).
- Installs a program's own icon into the base theme, under a name
  within a domain it owns (§4.3).
- Carries a program's icon as an identifier in `.pgss.icon`, or sets
  one in `user.pgss.icon`, and never a picture (§4.5).

## A conforming system

- Has the base theme at `/usr/share/icons/base/`, providing every
  identifier of §4.A (§4.4).

## What conformance does not require

Conformance does not require a consumer to determine any file type
beyond a directory and an executable, to show thumbnails, to cache
anything, or to draw an icon at any particular size. It does not require
a provider to install more than the base theme.
