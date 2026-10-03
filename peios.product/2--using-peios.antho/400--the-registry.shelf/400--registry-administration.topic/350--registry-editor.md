---
title: Registry Editor
type: how-to
description: Browse the registry from the desktop — its keys as a tree, each key's values with their types, any value in full, and a word on anything you may not read.
related:
  - peios/registry-concepts/overview
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-security/access-control
  - peios/registry-tools/reg
---

**Registry Editor** shows the registry: its keys as a tree, and the values
of the key you pick. A *key* is a container in the registry, like a folder,
and a *value* is a named, typed piece of data in a key. It reads the
registry as you, so it shows what you may read, and it says what you may
not.

## Opening it

- From the launcher: start **Registry Editor**. It opens on `Machine`.
- From a program: `gxwi-registry-editor --key PATH` opens on the key at
  `PATH`, such as `gxwi-registry-editor --key 'Machine\System\Services'`.

The window's title names the key shown, such as **Registry Editor:
Services**.

## The keys

On the left is the tree. It starts from three keys:

- **Machine** holds the machine's own settings.
- **Users** holds each person's settings, under a key named for their SID,
  the number that identifies them. The tree shows whose each one is, such
  as **dana**, before the SID.
- **CurrentUser** is your own key under Users, by a shorter name.

Select **▸** beside a key to show the keys under it, and **▾** to hide them.
Select a key's name to show its values.

To go straight to a key, type its path in the box at the top and press
**Enter** or select **Go**. Write the path with `\` between the names, as
in `Machine\System\Services`; `/` works too. The tree opens down to the
key. A path with no key at it is refused, with the reason.

## The values

The middle shows the values of the key shown, each with its name, its type
and its data. The default value comes first, as **(Default)**: it is the
value a key can hold without a name.

Types are given in words:

| It says | Type | Shown as |
|---|---|---|
| Text | `REG_SZ` | the text |
| Text with variables | `REG_EXPAND_SZ` | the text, with any `%NAME%` left as written |
| Link | `REG_LINK` | the path the link points to |
| List of text | `REG_MULTI_SZ` | the items, separated by · |
| Number | `REG_DWORD` | the number, then in hexadecimal |
| Number, big-endian | `REG_DWORD_BIG_ENDIAN` | the number, then in hexadecimal |
| Large number | `REG_QWORD` | the number, then in hexadecimal |
| Bytes | `REG_BINARY` | the bytes, in hexadecimal |
| No type | `REG_NONE` | nothing |

The registry doesn't check that a value's data fits its type. Data that
doesn't fit, such as a number of the wrong length or text that isn't valid
UTF-8, is shown in red, as bytes.

## A value or a key in full

Select a value to see it in full in the pane on the right: its type, its
size, the *layer* its data came from, and all of its data. A layer is a
set of registry entries that can override another. Bytes are shown eight
to a row, after the offset of the first.

With no value selected, the pane describes the key: when it last changed,
how many keys and values it holds, and whether it is a link or is kept only
until the machine restarts. **Copy path** copies the key's path.

## Changes made elsewhere

The window watches the keys it shows. A value or key added, changed or
removed by a program or in a terminal appears within a moment, with no need
to refresh. **Refresh**, or **F5**, reads everything again.

## What you may not see

Each key has its own permissions, and the registry checks only the key
being opened, not the keys above it. So:

- A key you may not list shows **You may not list this key's subkeys.**
  under it in the tree. A key you may not read at all shows **You may not
  read this key.** where its values would be.
- You may still go to a key under one you may not list, by typing its path.
  The tree then shows it, in italics, under the key that couldn't be
  listed.

Some keys let you list their subkeys but not read their values, or the
other way round. Registry Editor shows whichever you may, and says which
you may not.

## In a terminal

`reg` does the same in a terminal. The tree is `reg ls` and `reg tree`, the
values are `reg get` on a key, and a value in full is `reg get KEY NAME`.
See [reg](~peios/registry-tools/reg).
