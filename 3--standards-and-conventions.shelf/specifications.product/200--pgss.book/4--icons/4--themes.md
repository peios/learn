---
title: Themes
description: What a theme is on disk, where the chain is set, how a consumer turns an identifier into a file, and what the base theme must provide.
---

A theme is a directory under `/usr/share/icons/`, named for the theme,
holding one file per identifier it provides:

```
/usr/share/icons/<theme>/<identifier>.svg
```

A theme's name has the form of an identifier (§4.3). A theme is flat: a
consumer MUST NOT look in subdirectories of a theme, and a provider
MUST NOT put anything there that a consumer is meant to find.

## Format

A theme's file is an SVG document. This version of the chapter
recognises no other format: a file with another extension is not an
icon, whatever it holds.

An icon is drawn at whatever size the consumer needs, so a provider
SHOULD draw for a square canvas and SHOULD make sure the picture reads
at 16 pixels. A consumer draws the document as an image and MUST NOT
run any script in it.

> [!NOTE]
> Vector icons are what let a theme be one flat directory: there is no
> ladder of sizes to arrange, and no index is needed to find the right
> rung. A raster format, if a later version admits one, is an extension
> of the file's name and not of the theme's shape.

## The base theme

The base theme is the directory `/usr/share/icons/base/`. Every system
MUST have it, and it MUST provide every identifier listed in §4.A.

The base theme is where a provider installs a program's own icon
(§4.3). Another theme MAY provide the same identifier, and is then
consulted first.

## The chain

The chain is the ordered list of themes a consumer looks in. It is set
in the registry, so that every consumer on the system looks in the same
places:

| Key | Value | Type | Meaning |
|---|---|---|---|
| `Machine\Generic\Icons` | `Themes` | `REG_MULTI_SZ` | Theme names, first consulted first |

A consumer MUST append the base theme to whatever the value names, and
MUST ignore the base theme where the value names it, so that the chain
always ends in the base theme and nowhere else. An entry that is not in
the form of an identifier, or names a directory that is not there, is
passed over. The value absent, or the key absent, is a chain of the base
theme alone.

A consumer reads the chain when it starts and MAY read it again. A
change to the chain takes effect for a consumer when it next reads it.

## Lookup

A consumer looks an identifier up by trying each theme in the chain, in
order, for a file named for the identifier, and takes the first it
finds. The lookup of an identifier no theme provides fails; §4.5 says
what a consumer does then.

A consumer MUST check the identifier's form before it looks it up
(§4.3). The form admits no `/` and no leading `.`, so a well-formed
identifier can name nothing outside the theme's directory.

## Caching

Nothing in this chapter requires a consumer to keep any state between
lookups, and the flat form of a theme is chosen so that none is needed.
A consumer that nevertheless remembers a lookup MUST notice when the
theme's directory or the chain changes, or MUST say, in its own
documentation, how stale a remembered result may be.
