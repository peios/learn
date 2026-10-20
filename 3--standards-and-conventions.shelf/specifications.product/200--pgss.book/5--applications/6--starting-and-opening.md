---
title: Starting and Opening
description: What a consumer runs to start an application bare or with a file, what it passes and how, which applications are candidates to open a file and which of them it picks, and what a consumer must take from the catalogue rather than from a request.
---

## Starting

To start an application, a consumer executes its `program` with its
`arguments`, in order, as the process's arguments after the program's
own name. Each argument is passed as one argument, byte for byte. A
consumer MUST NOT pass the program or the arguments through a shell,
MUST NOT split, join, quote or expand them, and MUST NOT look the
program up along a path: it is absolute.

What else the process is started with, its environment, its working
directory, its standard streams, what it is confined by, is the
consumer's. A compositor puts its display in the environment so that
the program can be an app; a consumer of another kind does whatever
its kind does.

A consumer MAY let a person add arguments of their own, as a launcher
does with the words typed after the application's name. They follow the
declaration's.

## Opening

To open a file with an application, a consumer starts it as above with
one more argument last: the file's path, absolute. A file's path is
never put anywhere but last, and there is no placeholder syntax in this
version: a declaration whose `arguments` contains `%f` or `{file}` has
an argument that is those characters.

An application whose `opens` contains a pattern that a file's media
type matches is a **candidate** to open the file. A media type matches
`type/subtype` when it is equal to it, ignoring case, and matches
`type/*` when its top-level type is `type`. How the consumer knows the
file's type is its own, as in PGSS Icons §4.6.

A consumer that opens a file offers the candidates, or picks one of
them; which it does is the consumer's. A consumer that picks MUST pick
the file's default when its type has one (§5.7), and picks by a rule of
its own only when it has none. A consumer that offers SHOULD offer the
default first, or otherwise show which it is. A consumer MUST NOT read
a default from anywhere §5.7 does not name.

An application with no `opens` is a candidate for nothing, and is
started bare.

## From the catalogue, not from the request

A consumer often starts an application because something asked it to,
and the something is not always trustworthy: a page in a browser, a
message from another process. A consumer that starts an application on
a request that names it by id MUST take the program and the arguments
from the catalogue as it stands at that moment, and MUST NOT take a
program or arguments from the request. The request says which
application; the declaration says what runs.

A request that names an id the catalogue has no usable declaration for
starts nothing.

> [!NOTE]
> This is why a declaration is data and never a command line, and why
> the program is matched by file (§5.5) and named by absolute path
> (§5.3). A consumer that follows this section cannot be made to run
> anything a package did not install, whatever it is asked.
