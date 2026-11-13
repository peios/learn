---
title: Tree Nodes
description: The catalog and each index as a tree of small files named by their hash, the three kinds of node, the bucket of a name, and why a lookup reads three files.
---

A repository's catalog and each of its indexes is a **tree**: three levels
of small text files, each named by the hash of its content and stored at
`trees/sha256/<hash>`.

## Package nodes

A package's node has a line for each of its versions in the tree:

```text
8.21.0-1 x86_64 sha256:… yanked
8.22.0-1 x86_64 sha256:…
```

Each line is the version, the architecture and the manifest's identity,
then, for a version taken back, ` yanked`, or ` deleted ` and a reason
(§5.36). A reason is one line, not empty.

In the catalog, a package's node holds every version published. In an index,
it holds one version for each architecture.

## Bucket nodes

A name falls in the **bucket** of the first two hexadecimal digits of the
SHA-256 hash of the name's bytes. A bucket's node has a line for each package
in the tree whose name falls in it: the name, a space, and the identity of
the package's node.

## The top node

The top node has a line for each bucket that holds a package: the bucket's
two digits, a space, and the identity of its node. The tree is named by the
identity of its top node.

## Form

Every node's lines are sorted by their bytes, with no line twice, and each
ends in a newline. A consumer MUST refuse a node whose bytes don't hash to
its name, or that isn't in this form, and a bucket's node that lists a name
from another bucket.

## Why a tree

Looking up a name reads three nodes, the top, a bucket and a package,
however many versions the tree holds. Publishing one package changes its
node, its bucket's and the top: every other node stays byte for byte as it
was, and a snapshot shares every node it can with `leading` and with other
snapshots.
