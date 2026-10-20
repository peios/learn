---
title: Terminology
description: The nouns this chapter is specified in — icon, identifier, theme, base theme, chain, subject, source.
---

**Icon.** A picture that stands for a thing: a program, a file, a kind
of file, a directory. In this chapter an icon is always referred to by
its identifier, and the picture is whatever the theme chain gives that
identifier.

**Identifier.** The name of an icon: a short string in the form of §4.3.
`generic`, `inode-directory` and `dev.peios.gxwi.hello` are identifiers.

**Theme.** A directory holding one picture per identifier it provides,
in the form of §4.4. A theme provides an identifier if the directory
holds a file named for it.

**Base theme.** The theme every system has, on which every other stands.
It is where a program's own icon is installed, and it provides every
identifier of §4.A.

**Chain.** The ordered list of themes a consumer looks in. The chain is
the system's, not the consumer's: it is set as §4.4 says, and it always
ends in the base theme.

**Subject.** The thing a consumer wants an icon for: a path on the
filesystem, usually. §4.5 gives the rules for a path; a specification
that gives icons to other kinds of subject says how they yield an
identifier.

**Source.** One place an identifier for a subject may come from: the
file's extended attribute, the section a program carries, the file's
name, the file's type. §4.5 lists the sources and the order they are
consulted in.

Terms defined in PCDS (security descriptor) and in the Peios Kernel
TRM (extended attribute) are used with the same meaning and are not
redefined. *Media type* is used as RFC 6838 defines it.
