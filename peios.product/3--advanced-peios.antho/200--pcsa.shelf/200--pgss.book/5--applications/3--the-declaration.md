---
title: The Declaration
description: One TOML file per application, named for its id, saying its title, its program, its icon, what it opens and whether it is listed — and what a consumer makes of one that is malformed.
---

A declaration is a file in the catalogue's directory (§5.4), named for
the application's id:

```
/usr/share/apps/<id>.toml
```

The file's name is the declaration's id. Nothing in the file repeats
it, so the two cannot disagree.

## The id

An id has the form of an icon identifier (PGSS Icons §4.3): 1 to 255
bytes of lowercase ASCII letters, digits, `.`, `_` and `-`, beginning
with a letter or a digit. A consumer MUST treat a file whose name,
before `.toml`, is of any other form as no declaration.

An id is reverse-DNS, within a domain the provider owns, in the form a
package is named in (PSPU §5.3): the package's own name, or a name
beneath it when one package ships more than one application. A provider
MUST NOT install a declaration under an id in another provider's
domain, and a package manager MAY refuse a package that would.

> [!NOTE]
> The id doubles as the default name of the application's icon. PGSS
> Icons §4.3 has a program's own icon named for its package in the same
> form, so the common case, one package, one program, one icon, needs
> no `icon` line and no second name.

## The file

The file is a TOML document whose top-level table has these keys:

| Key | Type | Meaning |
|---|---|---|
| `title` | string | What the application is called. One line, not empty. Required. |
| `program` | string | The file to run: an absolute path. Required. |
| `arguments` | array of strings | What the program is always started with, in order, before anything else. Empty when absent. |
| `icon` | string | The identifier of its icon (PGSS Icons §4.3). The id when absent. |
| `description` | string | One line on what it is for. None when absent. |
| `opens` | array of strings | The media type patterns it opens. Empty when absent. |
| `listed` | boolean | Whether a launcher lists it. `true` when absent. |

An example, complete for a file explorer:

```toml
title = "Gexora"
description = "Browse the files on this system"
program = "/usr/bin/gexora"
opens = ["inode/directory"]
```

A provider MUST write a declaration that a TOML 1.0 parser accepts, and
MUST NOT rely on any key not in the table above being read.

## What a consumer makes of it

A consumer MUST ignore a key it does not know. That is how a later
version of this chapter adds to a declaration (§5.8) without breaking
a consumer built to this one.

A declaration is **unusable**, and a consumer MUST treat it as no
declaration, when any of these holds:

- the file is not a TOML document a TOML 1.0 parser accepts
- `title` is absent, is not a string, is empty or is more than one line
- `program` is absent, is not a string, or is not an absolute path
- a key in the table is present with a value of another type

A consumer SHOULD say on its own log which file was unusable and why,
so that a broken package can be found, and MUST go on to the rest of
the catalogue.

A declaration that is merely odd is set right, not thrown away:

- an `icon` that is not in the form of an identifier is treated as
  absent, and the icon is the id
- an entry in `opens` that is not a media type pattern is left out
- leading and trailing whitespace on `title`, `description` and `icon`
  is not part of the value

`arguments` is passed as given, byte for byte, with no whitespace
splitting, no quoting and no expansion (§5.6). A declaration is data,
and no part of it is a command line.

> [!NOTE]
> The program is an absolute path and not a name looked up along a
> `PATH` on purpose. A launcher runs what a package installed, and a
> file of the same name earlier on somebody's path is not it.
