---
title: Extension
description: What may be added to this chapter without breaking a conforming consumer or provider, and what may not.
---

## Additive changes

The following are additive, and a consumer or provider built to this
version behaves correctly in their presence:

- A new identifier in §4.A. A theme that lacks it is a theme that does
  not provide it, which every consumer already handles.
- A new theme in the chain. A consumer built to this version looks in
  it like any other.
- A new source in §4.5, consulted after the type. A consumer built to
  this version draws `generic` where a newer one would draw the new
  source's icon.
- A new governing specification, consulted first under §4.5.

## Changes requiring a new version

- A new file format in a theme (§4.4). A consumer built to this version
  does not find the file, so the identifier is not provided, so every
  subject that relies on it is misdrawn as something further down the
  chain.
- A new meaningful form of identifier (§4.3), since the set is closed.
- A change to the order of §4.5, or a source inserted before the type.
  Two consumers on one system would then disagree about what a file
  looks like.
- A change to the form of an identifier.

## Reserved

The `pgss.icon` name, in the `user` extended-attribute namespace and as
the suffix of a section name, is this chapter's. A specification that
wants a file to carry something else MUST use another name.
