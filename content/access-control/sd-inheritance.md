---
title: How SD Inheritance Works
type: concept
order: 90
description: How ACEs propagate from parent directories to children using CI, OI, NP, and IO inheritance flags.
---

Setting access rules on every individual file in a directory tree would be impractical. **Inheritance** solves this — ACEs on a parent directory can automatically propagate to new objects created inside it. Set a policy once on a directory, and every file and subdirectory created within it receives that policy automatically.

## Containers and objects

Inheritance distinguishes between two kinds of items:

- **Containers** hold other items — directories, registry keys with sub-keys
- **Objects** are leaf nodes — files, registry values

This distinction matters because inheritance flags let you control whether an ACE propagates to child containers, child objects, or both.

## The inheritance flags

Each ACE can carry a combination of four flags that control how it propagates:

| Flag | Name | Meaning |
|---|---|---|
| **CI** | Container Inherit | This ACE propagates to child containers |
| **OI** | Object Inherit | This ACE propagates to child objects |
| **NP** | No Propagate | This ACE inherits to direct children only — it does not continue to grandchildren |
| **IO** | Inherit Only | This ACE does not apply to the container it is set on — it exists only to be inherited by children |

These flags are set on ACEs in the parent's DACL. When a new object is created inside the parent, the kernel looks at these flags to decide which ACEs the child receives.

## Common combinations

The flags are most useful in combination. Here are the patterns you will encounter most often:

| Flags | Meaning | Typical use |
|---|---|---|
| CI \| OI | Applies here and propagates to all children and grandchildren (both containers and objects) | The standard "apply to this folder and everything inside it" |
| CI \| OI \| IO | Does not apply here, but propagates to all children and grandchildren | Set a policy that only affects contents, not the directory itself |
| CI | Applies here and propagates to child containers only — files do not inherit | Policy that applies to subdirectories but not files |
| OI | Applies here and propagates to child objects only — subdirectories do not inherit | Policy that applies to files but not subdirectories |
| CI \| OI \| NP | Applies here and propagates to direct children only — does not continue deeper | One level of inheritance |
| CI \| OI \| NP \| IO | Does not apply here, propagates to direct children only | Policy for immediate contents only, not the directory itself |

## An example

A project directory needs this policy:

- Developers can read and write everything in the tree
- Auditors can read everything in the tree but not the directory itself

The directory's DACL:

```
Allow  Developers  FILE_READ_DATA | FILE_WRITE_DATA  (CI | OI)
Allow  Auditors    FILE_READ_DATA                    (CI | OI | IO)
```

When a file is created in this directory, it inherits:

```
Allow  Developers  FILE_READ_DATA | FILE_WRITE_DATA  (inherited)
Allow  Auditors    FILE_READ_DATA                    (inherited)
```

When a subdirectory is created, it inherits the same ACEs — and because CI is set, those ACEs continue to propagate to the subdirectory's own children. The policy flows through the entire tree.

The Auditors ACE has the IO flag on the parent, so it does not grant auditors access to the top-level directory itself — only to its contents.

## Inherited vs explicit

When an ACE is inherited by a child object, it is marked as **inherited**. This marking is preserved on the object and serves two purposes:

**Distinguishing origin.** Tools can show which ACEs were set directly on an object (explicit) and which came from a parent (inherited). This makes it clear where a rule originated.

**Ordering.** Inherited ACEs are evaluated after explicit ACEs in the canonical ordering. An explicit deny on a file takes precedence over an inherited allow from its parent directory.

## Inheritance happens at creation

Inheritance is evaluated when an object is created. The new object receives a copy of the parent's inheritable ACEs at that moment. If the parent's DACL is later changed, existing children are **not** automatically updated — they retain the ACEs they inherited at creation time.

Propagating changes to existing children is a separate operation, covered in the how-to documentation.
