---
title: What Each Preference Permits
description: What an indexer may record of an item under each preference, and what it must remove when a preference narrows.
---

An item's **name and properties** are what the file system says about it
without its data being read: its name and path, its type as found from
its name, its size, its times and its owner. An item's **contents** are
its data, and everything an indexer would derive from reading it: words,
embedded properties such as a photograph's camera or a song's title,
extracted text, and anything computed from those.

| Preference | The indexer MAY record | The indexer MUST NOT |
|---|---|---|
| `all` | Name, properties and contents. | (no restriction from this chapter) |
| `no-content` | Name and properties. | Read the item's data for indexing, or record anything derived from it. |
| `none` | Nothing. | Record the item at all, or read its data for indexing. |

For a directory, `no-content` and `none` concern the directory itself;
what they mean for the items beneath it follows from §8.3, under which
those items share the directory's preference unless they carry their own.

An indexer MUST apply the preference before it reads an item's data. A
preference narrowed after an item was recorded MUST be applied to what
is already recorded: an indexer MUST remove what the new preference does
not allow, within the time §8.3 permits.

A preference narrows what an indexer records. It grants no access: an
indexer that may not read an item under its own access control does not
read it, whatever the preference says.
