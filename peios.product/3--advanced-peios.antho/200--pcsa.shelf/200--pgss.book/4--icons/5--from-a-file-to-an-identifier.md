---
title: From a File to an Identifier
description: The sources a consumer consults for a path's icon — a governing specification, the owner's attribute, the program's section, the name, the type — in order, and the icon of last resort.
---

Given a path, a consumer finds the identifier to draw by consulting the
sources below in order, and taking the first identifier that the chain
provides (§4.4). A source that yields no identifier, or one the chain
does not provide, is passed over and the next is consulted. If every
source is passed over, the identifier is `generic`, which the base
theme provides (§4.A).

A consumer MUST consult the sources in this order and MUST NOT skip
one.

## A governing specification

A specification that says what a kind of file means to a desktop MAY
also say what icon it has. A consumer that implements such a
specification applies it first, and if it yields an identifier the
chain provides, that is the icon.

Such a specification MUST yield an identifier, to be looked up under
§4.4 like any other, and MUST NOT yield a picture.

> [!NOTE]
> This is the step by which a declaration that a program is an
> application, with a title and the types it opens, gives the program
> an icon. That declaration is another chapter's; this one only leaves
> it the first word.

## The owner's word

A file or directory MAY carry the extended attribute `user.pgss.icon`,
whose value is an identifier. The attribute is the word of whoever owns
the file, and is consulted second.

A consumer MUST treat a value that is not in the form of an identifier
as no value. A consumer MAY treat a value ending in a NUL byte as
though the NUL were absent.

Because the attribute is in the `user` namespace, whoever can write the
file can set it, and it can be set on regular files and directories
only. A file that cannot carry an attribute is drawn by the sources
that follow.

## The program's word

A regular file that is an ELF object MAY carry a section named
`.pgss.icon`, whose contents are an identifier, optionally followed by a
NUL byte and nothing else. The section is the word of whoever built the
program, and is consulted third.

A consumer finds the section by the object's section header table, by
name, and takes the first section of that name. A consumer MUST NOT
execute or load the object to find it, and MUST bound what it reads: a
header that points outside the file, a section header table of
implausible size, or a section longer than an identifier could be, is
no section.

A file that is not an ELF object, or is one without the section, is
drawn by the sources that follow.

> [!NOTE]
> The section holds a name and not a picture on purpose. A program that
> carried its own SVG could not be restyled by a theme, and a consumer
> listing a directory of programs would be handed a picture by every
> one of them. A name is a few bytes, and it is the theme's to draw.

## The name

The fourth source is the file's own name. For a directory the candidate
is `directory-` followed by the name; for anything else it is `file-`
followed by the name; in both the name is converted to lowercase ASCII
first. If the result is not in the form of an identifier, which is so
for any name with a space or a non-ASCII character in it, the source
yields nothing.

So a directory called `Documents` is drawn as `directory-documents` if
the chain provides it, and a file called `Makefile` as `file-makefile`.
Which such names a theme provides is the theme's business; a consumer
MUST NOT special-case any.

## The type

The fifth source is the file's type, which yields identifiers as §4.6
says.

## Symbolic links

A consumer that shows a symbolic link as the thing it points to
consults the sources for the target. A consumer that shows it as a
link consults them for the link itself, and a link, being unable to
carry an attribute, is then drawn by its name or its type. A link whose
target does not exist is drawn as `generic`.

## What an icon is not

An icon is what a thing looks like, and is chosen by parties that can
say anything. A consumer MUST NOT infer from a subject's icon what the
subject is, what it will do, or who made it. A file drawn as a program
is not thereby a program.
