---
title: Registry Editor
type: how-to
description: Browse and change the registry from the desktop — its keys as a tree, each key's values with their types and what the registry manual says of them, typed forms to edit them, new and deleted keys, permissions, and a word on anything you may not read or change.
related:
  - peios/registry-concepts/overview
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-security/access-control
  - peios/registry-tools/reg
---

**Registry Editor** shows the registry: its keys as a tree, and the values
of the key you pick, which you can change. A *key* is a container in the registry, like a folder,
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

## What the registry manual says

Packages document their keys and values in the registry manual, which
[`regman`](~peios/registry-tools/regman) shows in a terminal. Registry
Editor shows the same, at the foot of the pane:

- For a key, what it is for, and the values documented for it that aren't
  set here, each with its default and what it does. **Set…** beside one
  starts a new value with that name and the type the manual gives it.
- For a value, the type the manual expects, its default, the values it
  may take, and when a change applies: at once, when the program that
  reads it next starts, or when the machine next starts. Then what it is
  for.

If a value's type isn't the one the manual expects, the pane says so in
red, since whatever reads it may not accept it. A key or value the manual
doesn't mention says so too.

## Changing values

To change a value, double-click it, or select it and choose **Edit…** in the
pane or on its right-click menu. The pane shows a form for its type:

- **Text** and **Link** take one line.
- **List of text** takes one item to a line. Empty lines are left out.
- **Numbers** take a whole number, typed in **Decimal** or
  **Hexadecimal**. Changing between them rewrites the number in the other
  form.
- **Bytes** take two hexadecimal digits to a byte. Spaces and new lines
  are ignored.

Data that doesn't fit its type is edited as bytes, and keeps its type.
**Save** writes it, and **Cancel** or **Esc** leaves it as it was.

If someone else changes the value while you're editing it, **Save**
refuses, and the list shows the value as it now is. Select **Save** again
to replace their change with yours.

**New value…** adds a value to the key shown. Give it a name, or leave the
name empty for the key's default value, and pick its type: text, text
with variables, a list of text, a number, a large number or bytes. A name
the key already uses is refused.

To delete a value, select it and choose **Delete…**, then confirm.

## Changing keys

- **New key…** creates a key under the one shown, and shows it.
- **Delete key…** deletes the key shown and everything under it, keys and
  values, after asking. It is all or nothing: if any part can't be
  deleted, nothing is. Links under it are deleted; the keys they point to
  are not. A key with more than about a thousand keys under it can't be
  deleted at once; delete some of them first.

The root keys can't be deleted. Changes go to the base layer, the one
every change goes to unless it names another.

The key shown has these on its right-click menu in the tree too, with
**Copy path**.

## Permissions

Each key has its own permissions, which say who may read it, change it
and so on. **Permissions…** in the pane, or on the key's right-click
menu, opens them in the permissions editor. **Read** covers reading the
key's values and listing the keys under it, and **Write** covers changing
values and creating keys. Each person or group added to a key applies to
the keys under it as well.

Some values hold a security descriptor: a list of who may do what, kept
for a program that reads it, such as a service's `ServiceSecurity`.
Registry Editor recognises one by its bytes, and shows it as **Security
descriptor**, written in SDDL, a short text form, rather than as bytes.
**Permissions…** beside it opens it in the permissions editor. What its
rights mean is the reading program's to say, so only the general ones
are named there: **Full control**, **Read**, **Write** and **Execute**.
Anything else it grants is shown as special and kept as it is. To change
one, you need to be allowed to change the key's values; otherwise it
opens read-only and says why. For a service's own permissions, Services
Manager names its rights properly: see [Who can manage a
service](~peios/services-and-jobs/who-can-manage-a-service).

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

What you may change of a key is its own permissions' to say: changing its
values, creating keys under it and deleting it are each a separate right.
Registry Editor asks the registry which of them you hold. What you may
not do is still shown, greyed out, and the pane says why, such as **You
may read this key but not change it.**

## In a terminal

`reg` does the same in a terminal. The tree is `reg ls` and `reg tree`, the
values are `reg get` on a key, and a value in full is `reg get KEY NAME`.
Saving a value is `reg set`, a new key is `reg new`, and deleting is
`reg del`, with `-r` for a key and everything under it. See
[reg](~peios/registry-tools/reg).
