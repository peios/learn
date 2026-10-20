---
title: From a Program to its Declaration
description: How a consumer that has met a program — a running process, or a file — finds the application it is declared as, and so its title and icon.
---

A consumer often meets a program before it meets a declaration: a
compositor sees a process connect, a taskbar is told of its windows, a
file explorer lists an executable. This section says how such a
consumer finds the declaration, if there is one, and what it gets from
it.

## Matching

A program matches a declaration when the program's file and the
declaration's `program` are the same file. Two paths name the same file
when they resolve, through every symbolic link, to the same path, or
when they refer to the same inode on the same device. The second is for
a system that presents one file at more than one path, as Peios' merged
views do (`/bin` over `/usr/bin`).

A consumer MUST match by file and MUST NOT match by name: a file called
`gexora` anywhere is not thereby Gexora.

For a running process, the program's file is the executable the process
is running, which on Peios is reached through `/proc/<pid>/exe`. A
consumer SHOULD match through the process rather than through the path
the process was started by, since the path may since have been
replaced.

When more than one declaration names the same program, the consumer
takes the one whose id sorts first, byte by byte. A provider SHOULD NOT
declare one program twice.

## What the match gives

A program that matches a declaration **is** that application, and a
consumer showing it to a person SHOULD show the declaration's title
where it names the program as a whole, such as under a dock's icon,
whatever its windows are called. A window keeps its own title.

The declaration gives the program its icon. Under PGSS Icons §4.5, this
chapter is a governing specification, and the identifier it yields for
a program is the declaration's `icon`. A consumer that implements both
chapters consults it first: if the chain provides the identifier, that
is the icon, and if not, the consumer goes on to the sources §4.5 lists
after it. A program that matches no declaration is drawn by those
sources alone.

A consumer MUST NOT infer from a match anything the declaration does
not say. In particular, a declaration says nothing about who built the
program or whether it is trusted; it says what a package chose to call
it.
