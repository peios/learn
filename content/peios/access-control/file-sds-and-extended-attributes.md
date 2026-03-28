---
title: File SDs and Extended Attributes
type: concept
order: 180
description: How file and directory security descriptors are stored as filesystem extended attributes.
---

Every file and directory on Peios has a security descriptor. For files, that security descriptor is stored in a **filesystem extended attribute (xattr)** — a named blob of data attached to the file's inode alongside the file's contents.

## How file SDs are stored

The security descriptor is stored as a binary blob in a dedicated extended attribute. The format is the standard self-relative SD format — the same binary structure used everywhere else in the system. The filesystem treats it as opaque data; the kernel's access control layer reads and writes it.

Extended attributes are supported by the filesystems Peios uses. They persist across reboots, survive file copies (when the copy tool preserves xattrs), and are backed up alongside the file's data.

## When the SD is read

The kernel reads a file's SD from its extended attribute when an access decision is needed — typically when the file is opened. The SD is not kept permanently in memory for every file on disk. It is loaded on demand, evaluated by AccessCheck, and the result (the granted access mask) is stored on the open file handle.

## How files get their SDs

When a new file is created, it receives an SD through the same process as any other object:

1. The **creating token** provides the owner SID, primary group SID, and default DACL
2. The **parent directory's SD** provides inheritable ACEs
3. An **explicit SD** at creation time overrides the defaults

The resulting SD is written to the file's extended attribute at creation time. The file is never accessible without a security descriptor — the SD is written atomically as part of file creation.

## Directories work the same way

Directories store their SDs in extended attributes just like files. The difference is that directory SDs can contain inheritable ACEs that propagate to child files and subdirectories created within them.

## What happens if the xattr is missing

A file without an SD extended attribute has no security policy. This should not occur during normal operation — every file creation path writes an SD. If it does occur (for example, a file created by an external tool that does not understand Peios SDs), the kernel synthesizes a default SD from system policy to ensure the file is never unprotected.
