---
title: Closures
description: Packages composed into one tree of hard links, the contents of a /usr, the conflicts that stop one being built, how one is named, and why an existing one is reused.
---

A **closure** is a set of packages composed into one directory tree: the
contents of a `/usr`. Mounted at `/usr`, each package's files are at their
ordinary paths.

## The tree

Every file of a closure is a hard link to its blob in the form its entry
needs (§5.12), which carries the entry's security metadata. Symbolic links
and directories are created in the tree, each directory with its
descriptor, and so is each link a package claims under `/usr` (§5.23). A
closure is only `/usr`, so links claimed elsewhere are left out of it.

A closure MUST be on the same filesystem as the artifact directory its
blobs are in. A consumer MAY copy each file from its blob instead, checking
it against its hash as it does, and giving it the entry's security metadata;
it MUST NOT fall back to copying without being asked.

The tree's root grants everyone read and execute, and what is created in it
inherits that. Its files have the access their blobs grant.

The closure's inventory (§5.25) is at the top of the tree, as `inventory`.

## Conflicts

Every package's paths are merged before anything is written, and a consumer
MUST refuse to build the closure, writing nothing, if:

- two packages give one path different entries, even entries that differ
  only in their security metadata;
- a path lies beneath a file or link of another package, or beneath a
  claimed link;
- a claim breaks §5.23's rules;
- a package holds or claims `/usr/inventory` (§5.13).

The result doesn't depend on the order the packages are given in.

## Name

A closure is named by the identity of its inventory without the inventory's
first line (§5.25): its packages and what wants each. The same packages
asked for the same way are always the same closure; the same packages asked
for differently are another. A closure's tree is `closures/<hash>/` in the
artifact directory, and its manifest, those same lines, is
`closures/<hash>.manifest`.

## Reuse

Because a closure's name is known before it is built, a consumer MUST reuse
one that exists rather than build it again, after checking that its
manifest is the one its name hashes to. A closure is built in a temporary
directory beside where it goes and renamed into place when complete, so one
that exists is never half-built. Reusing one only reads it.
