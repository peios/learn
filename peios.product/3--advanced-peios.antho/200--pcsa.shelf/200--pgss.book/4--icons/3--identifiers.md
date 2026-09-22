---
title: Identifiers
description: The form of an icon's name, the prefixes that carry meaning, and which names a program may take for its own.
---

An identifier is a string of 1 to 255 bytes, each a lowercase ASCII
letter, an ASCII digit, `.`, `_` or `-`, whose first byte is a letter or
a digit:

```
identifier = first *254 rest
first      = %x61-7A / %x30-39
rest       = first / "." / "_" / "-"
```

A consumer MUST treat a string of any other form as no identifier: it
is not looked up, and the source it came from is passed over as though
it had said nothing (§4.5). This is what keeps a name from naming a
path: no identifier contains `/`, and none begins with `.`.

Identifiers are compared byte for byte. There is no case folding,
because there is no case.

## Meaningful forms

Some forms of identifier are given meaning by this chapter, and a
provider MUST NOT use them for anything else:

| Form | Meaning | Defined in |
|---|---|---|
| `generic` | The icon of last resort | §4.5 |
| `directory-<name>` | A directory called `<name>` | §4.5 |
| `file-<name>` | A file called `<name>` | §4.5 |
| `<type>-<subtype>` | A file of that media type | §4.6 |
| `<type>` | A file of any subtype of that media type | §4.6 |

The set is closed. A future version of this chapter MAY add a form; a
provider MUST NOT invent one.

## A program's own

A program's own icon is named for the program, in the reverse-DNS form
its package is named in (PSPU §5.3): `dev.peios.gxwi.hello`. The
package that installs the program installs the icon into the base
theme under that name, and the program carries the name (§4.5).

A provider MUST NOT install an icon under a name that is another
provider's, and a package manager MAY refuse a package that would. The
reverse-DNS form makes that a matter of who owns the domain.

> [!NOTE]
> The standard names of §4.A, the forms above and reverse-DNS names
> cannot collide: a reverse-DNS name has a dot in its first label
> position where the others have a hyphen or nothing. A theme can
> therefore provide all three kinds in one flat directory.
