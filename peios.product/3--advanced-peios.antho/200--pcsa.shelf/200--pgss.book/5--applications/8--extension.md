---
title: Extension
description: What may be added to this chapter without breaking a conforming consumer or provider, and what may not.
---

## Additive changes

The following are additive, and a consumer or provider built to this
version behaves correctly in their presence:

- A new key in a declaration (§5.3). A consumer built to this version
  ignores it, and a declaration that carries it is usable by that
  consumer as far as the keys it knows go. A new key MUST be optional,
  and its absence MUST mean what this version's consumers do.
- A new kind of consumer. A provider has nothing to do for it.
- A new declaration in the catalogue, and a new provider.
- A second place for declarations, consulted after the catalogue, such
  as a person's own. A consumer built to this version does not see it,
  and shows the system's applications where a newer one would show
  more.
- A subkey of a key of §5.7, or a new key beside `Defaults` under
  either `Applications` key. A consumer built to this version ignores
  them, and finds the same defaults as before.

## Changes requiring a new version

- A change to the catalogue's directory, or a subdirectory a consumer
  is meant to look in (§5.4). A consumer built to this version does not
  find what is there.
- A new file format or extension for a declaration (§5.3).
- A meaning for any sequence of characters in `arguments`, such as a
  placeholder for a file. A consumer built to this version passes it
  through as it is, so an application that relied on it would be
  started wrongly.
- A place for the file's path other than last (§5.6).
- A change to what makes a declaration unusable (§5.3), or to the
  match rule (§5.5). Two consumers on one system would then disagree
  about what is installed, or what a program is.
- A change to where choices are kept, to the form of a choice, or to
  the order they are tried in (§5.7), including a place for choices
  consulted between the person's and the machine's, such as a group's.
  Two consumers on one system would then open one file with different
  applications.

## Reserved

The directory `/usr/share/apps/` is this chapter's, and so is the
`.toml` extension within it. The keys named in §5.3 are this chapter's:
a specification or a provider that wants a declaration to carry
something else MUST use another key, and SHOULD prefix it with a domain
it owns.

The registry keys `Machine\Generic\Applications` and
`CurrentUser\Generic\Applications`, and everything in them, are this
chapter's. Nothing else may keep anything there.
