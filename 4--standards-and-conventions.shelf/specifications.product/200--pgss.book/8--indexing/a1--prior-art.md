---
title: Prior Art
description: Where this chapter sits against Windows' not-content-indexed attribute, macOS's Spotlight exclusions, and the per-directory marker files of Linux tools.
---

## Windows

Windows keeps one bit per item, `FILE_ATTRIBUTE_NOT_CONTENT_INDEXED`. A
folder's bit is copied onto items created in it, and changing a folder
asks whether to change what it already holds. This chapter keeps the
meaning of the bit as `no-content`, and adds `none` for keeping an item
out of search entirely, which Windows does only by excluding a location
from the indexer's own configuration.

The chapter does not copy a folder's word onto new items. Linux has no
way to give a new file an extended attribute from its directory, so a
copied word would hold only for files made by programs that know to copy
it. A word that holds for everything beneath a directory needs no
copying and covers every program.

## macOS

Spotlight skips a directory whose name ends in `.noindex`, or which holds
a file named `.metadata_never_index`, and keeps a list of excluded
locations in its own settings. The marker-file form is the same idea as
§8.3: a directory says something about everything beneath it. An
extended attribute serves better than a marker file, because it does not
appear in listings and goes with the directory when it is moved.

## Marker files on Linux

`.nomedia` (Android media scanners), `CACHEDIR.TAG` (backup tools) and
`.gitignore` all let a directory speak for its subtree. This chapter
takes their nearest-word rule, and lets a nearer word loosen a farther
one as a `.gitignore` negation does.

## Design influences

**Less when unsure.** A value an indexer does not recognise narrows what
it records, because the cost of a wrong guess is uneven: an item missing
from search is found another way, and contents recorded against their
owner's wish cannot be unrecorded from whoever saw them.

**The owner's word, not the indexer's.** The preference is on the item,
so it travels with the item and binds every indexer, rather than being
one indexer's setting that another ignores.
