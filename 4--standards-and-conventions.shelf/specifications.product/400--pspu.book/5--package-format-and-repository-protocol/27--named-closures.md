---
title: Named Closures
description: A name in a closure directory that points at one of its closures, how it is changed, and the two names an installed system uses.
---

A closure can be given a **name** of its own, so that what a system runs can
be chosen, and changed, by name.

## Form

A name is a symbolic link in the closure directory, `closures/<name>`, whose
target is the closure's hash: the name of its tree beside it. A name follows
§5.9's rules for closure names.

A consumer MUST change a name by creating a new link elsewhere in the
closure directory and renaming it over the old one, so that the name always
names one closure or another, never neither. A name MUST NOT be set to a
closure that doesn't exist.

Removing a name leaves its closure. A consumer that lists a closure
directory MUST tell names, which are symbolic links, from closures, which
are directories.

## Reserved names

| Name | Names |
|---|---|
| `SYSTEM` | The closure that is an installed system's `/usr` |
| `INITRAMFS` | The closure an installed system's initramfs is built from |

How an installed system boots from them is outside this chapter.
