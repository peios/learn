---
title: Applying
description: When an applier applies the file, what it makes, what it leaves alone, and how it creates a directory with a descriptor.
---

An applier applies a root's skeleton file after installing the root's
packages, and before running anything from the root. It reads the file
from the root it is building, never from the system it is running on.

## Check first

An applier MUST read the whole file before it changes the root. It
checks every line against §11.3 and every descriptor it will apply. A
file with any error is rejected whole, and nothing is made.

## Make what is missing

The applier then takes each entry in order:

| What is at `path` | Directory entry | Link entry |
|---|---|---|
| Nothing | Create the directory | Create the link |
| A directory | Leave it | Fail |
| A link | Fail | Leave it if its content is `target`, otherwise fail |
| Anything else | Fail | Fail |

The applier MUST NOT follow a link at an entry's path, and MUST NOT make
an entry by way of a link. The order rule (§11.3) means each entry's
parent is the root or a directory the applier has already found or made.

An applier MUST NOT delete anything, and MUST NOT change anything it
finds, including an existing directory's descriptor. Applying the same
file twice makes nothing the second time.

On a failure, the applier stops and reports the entry and the reason.
What it made before the failure stays. Applying the file again, once
the obstacle is removed, continues from where it stopped.

## Descriptors at creation

An applier MUST create a directory that has a descriptor with that
descriptor, in the same operation that creates it. On Peios this is the
kernel's native create, `kacs_open`, with the descriptor supplied as the
new directory's. It MUST NOT create the directory and then set its
descriptor, because the directory would have an inherited descriptor in
between.

An applier building a tree whose format holds no descriptors, such as an
initramfs archive, creates each directory without one. The descriptors
then have no effect in that tree. It still checks every descriptor's
syntax where it can, but it MUST NOT reject the file only because it
cannot apply the descriptors.

## A root without a file

A root whose closure holds no skeleton file gets nothing from this
chapter. An applier SHOULD warn that the root has no skeleton file, and
MAY continue.
