---
title: Tree Nodes
description: The catalog and each index as a tree of small files named by their hash, the three kinds of node, the bucket of a name, each version's summary, the catalog's provides tree, and why a lookup reads three files.
---

A repository's catalog and each of its indexes is a **tree**: three levels
of small text files, each named by the hash of its content and stored at
`trees/sha256/<hash>`.

## Package nodes

A package's node has a line for each of its versions in the tree:

```text
8.21.0-1 x86_64 sha256:<manifest> sha256:<summary> yanked
8.22.0-1 x86_64 sha256:<manifest> sha256:<summary>
```

Each line is the version, the architecture, the manifest's identity and
the identity of the version's summary, then, for a version taken back,
` yanked`, or ` deleted ` and a reason (§5.36). A reason is one line, not
empty. The two identities are told from what follows them by their
`sha256:` prefix. A deleted version's line MAY lack its summary; every
other line MUST have one.

This form replaces the one without summaries: a consumer MUST refuse a
line of a version not deleted that lacks one. A publisher reading a catalog
or an index written without them, to publish again, writes it with them
(§5.36).

## Summaries

A version's **summary** is its manifest's head: every byte of the manifest
before the blank line that comes before `[files]` (§5.18). It holds the
package's ID and all of its metadata, and so everything resolution needs,
but not its files. A summary is stored as a node of its own, at
`trees/sha256/<hash>`, named by the hash of its bytes.

A consumer MUST refuse a summary that doesn't hash to its name, or that
isn't a manifest's head in the one form (§5.18), or that names another
version than the line that gives it. A consumer that reads a manifest
whose summary it resolved from MUST refuse it unless the manifest begins
with that summary, followed by a blank line and `[files]`.

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

## The provides tree

A catalog has a **provides tree**, whose top the pointer file names
(§5.32). It has the same three levels, but its leaves are capabilities
(§5.4), not packages: a capability falls in the bucket of the first two
hexadecimal digits of the SHA-256 hash of its name, and a capability's node
has a line for each version, of any package, that provides it:

```text
org.gnu.glibc 2.44-1 x86_64 2.44
org.git.kernel.dash 0.5.13.5-1 x86_64 -
```

Each line is the package's name, its version and architecture, and the
version it provides the capability at, or `-` for none. Every version the
catalog lists and hasn't deleted is in it, yanked or not, for every
capability it provides: each its `provides` table lists, and its own name
at its own version unless the table lists that too (§5.21). A version's
standing is in the catalog's package node, not here.

## Why a tree

Looking up a name reads three nodes, the top, a bucket and a package,
however many versions the tree holds, and finding what provides a
capability reads three more. Publishing one package changes its
node, its bucket's and the top: every other node stays byte for byte as it
was, and a snapshot shares every node it can with `leading` and with other
snapshots.
