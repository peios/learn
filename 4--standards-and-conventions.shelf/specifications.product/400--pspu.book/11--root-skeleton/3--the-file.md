---
title: The File
description: Where the skeleton file is, how its lines are read, the two kinds of entry, and the rules every path, link target and descriptor follows.
---

The skeleton file is at `/usr/share/skeleton` in the root it describes.
A root has at most one, because one path in a closure belongs to one
package. It is UTF-8 text, with lines separated by a line feed (U+000A).

```text
# Directories outside /usr, each after its parent.
/var
/var/state
/var/state/secrets O:SYG:SYD:P(A;OICI;GA;;;SY)
/lib64 -> usr/lib/x86_64-linux-peios
```

## Lines

A line is read after removing leading and trailing spaces (U+0020) and
tabs (U+0009). A line that is then empty, or that begins with `#`, is
ignored. A comment occupies a whole line; `#` later in a line is not a
comment.

Every other line is an entry. Its fields are separated by one or more
spaces or tabs, and it has one of three shapes:

| Shape | Entry |
|---|---|
| `path` | A directory with no descriptor. |
| `path descriptor` | A directory created with `descriptor`. |
| `path -> target` | A symbolic link at `path` whose content is `target`. |

A line of any other shape makes the file invalid.

## Paths

Each `path` MUST:

- begin with `/` and name something under the root, not the root itself;
- be in canonical form, with no empty, `.` or `..` component and no
  trailing `/`;
- be outside `/usr`, neither `/usr` nor anything under it.

No two entries may have the same `path`.

## Order

Entries are applied in the order the file gives them. The parent of each
entry's `path` MUST be the root, or a directory entry earlier in the file.
A file that lists a child before its parent, or under a link, is invalid.
A provider can list paths in byte order to satisfy this, because a
parent's path is a prefix of its children's.

## Link targets

A `target` is the link's content, exactly as written. It MUST be
relative: it is resolved from the directory holding the link, so the link
works wherever the root is mounted, including while it is being built.
It MUST NOT have an empty component, and following its `..` components
from the link's directory MUST NOT go above the root.

## Descriptors

A `descriptor` is a security descriptor in SDDL. It has no spaces or
tabs. It SHOULD name principals only by well-known SIDs or absolute SID
aliases, such as `SY` or `BA`. The file is applied before any domain or
machine exists to resolve anything else.

A directory without a descriptor inherits one from its parent, as any
new directory does.

A descriptor MUST grant whoever applies the file a right to read the
directory. Root builders run as SYSTEM, so a descriptor that grants
SYSTEM full control is enough.
