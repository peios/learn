---
title: The Catalogue
description: The directory of declarations, read whenever a consumer needs the list — no registration, no index, no cache required.
---

The catalogue is the directory `/usr/share/apps/`. Every system MUST
have it, and it MUST be readable by anyone who can log on to a desktop:
every consumer reads it as the person it runs for.

The catalogue is flat. A consumer MUST NOT look in subdirectories of
it, and a provider MUST NOT put anything there that a consumer is meant
to find. A file in it whose name does not end in `.toml`, or whose name
before `.toml` is not in the form of an id (§5.3), is not a declaration
and MUST be passed over.

## Presence is the catalogue

A declaration is in the catalogue when its file is in the directory,
and out of it when the file is gone. Nothing else is required of a
provider: no command at install, no index to rebuild, no notice to any
consumer. A package that installs a declaration has shipped an
application, and one that removes it has withdrawn it.

A consumer MUST NOT require a provider to do anything beyond installing
the file.

## Reading it

A consumer that needs the list reads the directory, and reads each
declaration by the rules of §5.3. A consumer that needs one application
by id MAY read that file alone, at `<id>.toml`, after checking the
id's form: the form admits no `/` and no leading `.`, so a well-formed
id can name nothing outside the directory.

A consumer SHOULD leave out of any list a declaration whose program is
not a regular file. Nothing is there to start, and a package that is
half installed or half removed should not be offered.

A consumer MAY order what it lists however it likes; a provider MUST
NOT rely on any order.

## Caching

Nothing in this chapter requires a consumer to keep any state between
reads, and a catalogue of a few hundred files is meant to be read
whenever a launcher opens. A consumer that nevertheless remembers what
it read MUST notice when the directory changes, or MUST say, in its own
documentation, how stale a remembered result may be.

> [!NOTE]
> This is the shape of PGSS Icons' theme (§4.4): a flat directory that
> is its own index. The desktop-file databases that other systems rebuild
> after every install exist because those catalogues could be anywhere and
> hold anything; a catalogue that is one directory of small files needs none.
