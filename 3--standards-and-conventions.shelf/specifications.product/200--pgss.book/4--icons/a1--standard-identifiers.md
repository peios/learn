---
title: Standard Identifiers
description: The identifiers the base theme provides on every system, so that a consumer always has something to draw.
---

The base theme MUST provide every identifier below (§4.4). Another theme
MAY provide any of them. The set is closed for this version; a later
version MAY add to it (§4.7).

## Last resort

| Identifier | Drawn for |
|---|---|
| `generic` | Anything no other source gives an icon (§4.5) |

## Types

The identifiers the two types every consumer determines yield (§4.6),
and the top-level types a consumer is most likely to determine from a
name.

| Identifier | Drawn for |
|---|---|
| `inode-directory` | A directory |
| `application-x-executable` | A program |
| `application` | A file of any other `application/` type |
| `text` | A file of any `text/` type |
| `image` | A file of any `image/` type |
| `audio` | A file of any `audio/` type |
| `video` | A file of any `video/` type |

## Named directories

The directories a person is most likely to keep, by the names they are
most likely to have (§4.5).

| Identifier | Drawn for |
|---|---|
| `directory-documents` | A directory called `Documents` |
| `directory-downloads` | A directory called `Downloads` |
| `directory-pictures` | A directory called `Pictures` |
| `directory-music` | A directory called `Music` |
| `directory-videos` | A directory called `Videos` |
