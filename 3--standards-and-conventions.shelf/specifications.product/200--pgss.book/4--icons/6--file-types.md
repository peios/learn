---
title: File Types
description: How a file's media type yields identifiers, in what order they are tried, and the two types every consumer can determine.
---

A file's type is a media type, `text/x-python`, `image/png`,
`inode/directory`. How a consumer determines it is outside this
chapter: by the file's name, by its contents, by a table of its own, or
by asking something else. This chapter says only what a type yields
once known.

## From a type to identifiers

A media type yields two identifiers, tried in order:

1. The whole type, `<type>/<subtype>`, with `/` replaced by `-`.
2. The top-level type alone.

Any character in either that is not permitted in an identifier is
replaced by `-`, and the result is lowercase. So `image/svg+xml` yields
`image-svg-xml` and then `image`, and `text/x-python` yields
`text-x-python` and then `text`. The second lets a theme draw every
kind of text alike and still draw Python apart when it cares to.

A consumer MUST try both, in that order, and pass on to `generic`
(§4.5) when the chain provides neither.

## Types every consumer determines

Whatever else it knows, a consumer MUST determine these:

| The file is | Type |
|---|---|
| A directory | `inode/directory` |
| A regular file that may be executed, and nothing better is known | `application/x-executable` |

"May be executed" means what it means to the system the consumer runs
on; on Peios, that the file's security descriptor grants the consumer
execute access.

## Determining a type

A consumer MAY determine a type from the file's name alone, and a
consumer listing a directory usually should: reading every file to
sniff its contents is the cost that a name is meant to spare. A
consumer that reads contents MUST bound what it reads.

> [!NOTE]
> There is no system-wide table of types in this version. A consumer
> ships its own, which is enough for icons: a type a consumer does not
> know is drawn as `generic`, and nothing is misdrawn. A shared table is
> a matter for whichever chapter first needs two consumers to agree on
> what a file *is*, which is more than what it looks like.
