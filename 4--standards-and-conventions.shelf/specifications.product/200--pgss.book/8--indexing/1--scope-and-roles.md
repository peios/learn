---
title: Scope and Roles
description: What PGSS Indexing specifies, a per-item preference for how far search may index a file or directory, and the two roles that set and honour it.
---

This chapter specifies **PGSS Indexing**: how the owner of a file or
directory says how far a search index may record it, and how an indexer
honours what they said.

The chapter rests on one decision. The preference is a word on the item,
in an extended attribute, and a directory's word holds for everything
beneath it. One word on a folder keeps a whole tree out of search,
whatever program later creates files in it, without anyone marking each
file.

Two roles participate.

The **marker** says how an item may be indexed, by setting or removing
the attribute. A person running a command, a file manager with a
checkbox, and a file server translating a client's request are all
markers.

The **indexer** builds a record of files that people can search: their
names, their properties, their contents. A desktop search service and a
file server's search are indexers. Before it records anything of an item
it finds the item's preference by the rules of §8.3, and records no more
than the preference allows (§8.4).

Both roles are publicly implementable. A third party MAY ship a marker or
an indexer and interoperate with the rest unchanged.

This chapter covers:

- the attribute and the words it may hold (§8.2)
- how an indexer finds an item's preference from the item and the
  directories above it (§8.3)
- what each preference permits an indexer to record (§8.4)
- how a marker translates Windows' "not content indexed" attribute (§8.5)

This chapter does not cover:

- Who may search an index, or what a search returns to whom. An indexer
  answers searches under its own access control.
- Which locations an indexer covers at all. An indexer chooses where it
  looks; this chapter only narrows what it records where it does look.
- Thumbnails, previews and caches that are not a search index.
- Hiding a file from listings. A preference narrows search only; the
  item stays visible to anyone who can list its directory.
