---
title: Payload Entries
description: The three kinds of entry a manifest lists, files, symbolic links and directories, what a file records of its mode, and a file's detached PIP signature.
---

A manifest's `[files]` table lists every path of the package with an
**entry**: a file, a symbolic link, or a directory.

## Files

A file's entry names its content's blob (§5.12) by identity, and records
whether it is executable: whether any execute bit was set on the file it
was packed from. That is all a package records of a file's mode. Owner,
group, the other permission bits and timestamps are not part of a package:
access is governed by security descriptors (§5.20).

A producer MUST refuse to pack a file with its set-user-ID or set-group-ID
bit set, and anything that is not a regular file, a symbolic link or a
directory, such as a socket or a device.

## Symbolic links

A link's entry records its target exactly as `readlink` returns it
(§5.17).

## Directories

A directory is implied by the paths beneath it. A directory with nothing
beneath it is listed, so that it is created, and so is a directory with a
security descriptor (§5.20), whatever is beneath it. Every other directory
is left out of the manifest, so each tree has one manifest.

## One package per path

Within a closure, a path belongs to one package. Two packages MAY both list
a path only if their entries for it are identical, security metadata
included; §5.24 says what is refused.

## Detached signatures

A file the kernel loads as firmware is checked against its PIP signature,
which the kernel reads from the file's `security.peios.sig` extended
attribute (PSPK book 3). A package carries it as part of the file's entry:
the entry's `signature` names a blob holding the signature, which is 3310
bytes, starting with the version byte 1. A consumer that places the file
MUST give it that signature as its `security.peios.sig` attribute.

A producer takes a file's signature from the file beside it in the tree it
packs, named with `.peios.sig` added, which is not packed as a file of its
own. The file it signs MUST be a regular file that is not ELF: an ELF file
carries its signature in its own `.peios.sig` section. No other path MAY end
in `.peios.sig`.

## Forward compatibility

An entry has one of the three forms of §5.18, with exactly the keys that
section gives. A consumer MUST refuse an entry with any other key: this
version leaves no room for an entry it doesn't understand, since a closure
built without it would not be the package.
