---
title: Prior Art
description: Where this chapter sits against the freedesktop icon specifications, Windows shell icons and MSIX, and which resemblances are deliberate.
---

## The freedesktop icon theme and naming specifications

This chapter is, in outline, freedesktop's: an icon is a name, a theme
is a directory that gives names pictures, themes stand in a chain that
ends in `hicolor`, and a standard vocabulary lets one theme restyle a
whole desktop. What it drops is the size ladder and the index that the
ladder made necessary: with one vector file per name a theme is flat,
and there is no `icon-theme.cache` to rebuild. It also drops the
`Icon=` line of a desktop file as the only way a program gets a name,
in favour of the program carrying it.

The name source (§4.5) is not freedesktop's, which gives `Documents`
and `Downloads` their icons by configured path rather than by name. By
name is simpler and needs no configuration, and the editor icon themes
that colour a `src` directory apart from a `test` one show what it is
for.

## Windows

Windows puts the picture in the program: a PE file carries icon
resources, a shortcut or a registry `DefaultIcon` value points at
`path,index`, and the shell extracts what it finds. That gives a raw
executable an icon anywhere it is copied, which this chapter keeps by
having the program carry a name. It also makes every consumer a parser
of executables and every listing an extraction, which is why the shell
caches, and why this chapter has the program carry a name and not a
picture.

MSIX moved a packaged program's icons out of the binary into image
files named in the package manifest, which is the shape this chapter
gives a program's own icon: a file installed under a name the program
declares.

## Design influences

**One resolver.** Every source yields a name, and a name becomes a
picture in one place, so that a theme restyles programs as well as
folders, and so that two consumers on one system cannot disagree about
what a file looks like without one of them being wrong.

**The owner's word above the program's.** `user.pgss.icon` is consulted
before `.pgss.icon` because an attribute is set on a particular file by
whoever has it, and a section is set on every copy by whoever built it.
The particular overrides the general, as a custom folder icon overrides
the folder icon.

**A hint, not a claim.** Anyone who owns a file can make it look like
anything, as anyone can on any other system. The chapter says so once
(§4.5) so that no consumer is built to trust it.
