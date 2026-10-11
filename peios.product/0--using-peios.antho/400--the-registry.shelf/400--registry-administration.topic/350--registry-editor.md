---
title: Registry Editor
type: how-to
description: Inspect registry settings and their manual, choose a write layer, make a controlled desktop edit, and verify or recover the result.
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

## Before changing anything

1. Browse to the exact key and inspect its current values. Select a value
   to see its winning layer and the registry manual beside it.
2. Check the manual's expected type, valid values and application timing.
   A saved value can still be rejected by the component that reads it.
3. Check **Writes go to** in the bar. Your change goes to that layer,
   which may differ from the layer currently winning the value.
4. Record the original state. Use **Files → Back up…** if recovery needs
   key permissions and layered entries; **Export…** is a reviewable
   configuration document with different coverage.
5. Save one intended change, then [verify it](#verify-a-saved-change).

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

- For a key, what it is for.
- For a value, the type the manual expects, its default, the values it
  may take, and when a change applies: at once, when the program that
  reads it next starts, or when the machine next starts. Then what it is
  for.

Values the manual documents that aren't set on the key are listed after
the values that are, greyed, with **Not set** and the default the manual
gives, as in **Not set · default 30**. Check the manual for the consumer's
missing-value behavior; some retain a previously active value. These
manual-only entries aren't stored values, so they aren't counted or exported. Select one to see what the manual says of it, and double-click
it or choose **Set…** to start a new value with its name, the type the
manual gives it and, where the default is a plain value, the default.

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

If **Save** reports a concurrent change, it refuses the edit and refreshes
the list. Review the current value and destination layer before choosing
**Save** again; submitting your edit again can replace another writer's
entry in that layer. Conditional-write checks are scoped to the
destination layer, so do not assume they guard every change to another
layer's effective winner. See [Transactions](~peios/registry-advanced/transactions#avoid-overwriting-another-writer).

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
  are not. Large trees can exceed file-descriptor or transaction limits
  and be refused. Review the [deletion limits](~peios/registry-tools/reg#reg-del-key-value)
  and agree a smaller deletion scope before splitting the operation: separate
  deletions are no longer one atomic change.

The root keys can't be deleted. Changes go to the base layer, the one
every change goes to unless it names another.

The key shown has these on its right-click menu in the tree too, with
**Copy path**.

## Layers

A [layer](~peios/registry-layers/layers) is a set of registry entries
that can override another. **Layers…** in the bar opens them in a window
of their own, each with its precedence, whether it is enabled, and who
owns it. Where entries for the same value are in several layers, the one
in the layer of highest precedence wins; at equal precedence, the
most recent write to that value wins. Different values can have different
winning layers.

- **New layer…** creates one. A layer may be disabled from the start: it
  then takes part only for programs that name it.
- **Disable** and **Enable** switch a layer off and on.
- **Set** gives a layer a new precedence.
- **Delete…** deletes a layer after asking, and every entry written into
  it goes with it.

A precedence above 0 needs the privilege to act as part of the operating
system (SeTcbPrivilege), which administrators don't hold, so for them only
0 may be set, and the window says so. The base layer is always there, at
precedence 0, and can't be changed.

**Writes go to**, in the bar, picks the layer your changes are written
into, base unless you choose another. You need to be allowed to write into
it as well as to change the key: if you may not, the key is shown
read-only, with the reason. Deleting a value deletes only that layer's
entry for it; another surviving entry can then show. Deletion does not
necessarily leave the value absent or select its documented default.

The pane says which layer a value's data came from. The registry can't
yet list a value's entries in the layers beneath the one that wins, so
only the winning entry is shown. If your changes go to a lower layer than
the one a value comes from, the pane warns that they won't show while
that entry is there.

## Permissions

> [!WARNING]
> Changing a key's permissions is not a layered edit. Disabling or deleting
> the selected layer does not restore the key's old owner or permissions.
> Existing open handles keep their granted rights until they are reopened.

Each key has its own permissions, which say who may read it, change it
and so on. **Permissions…** in the pane, or on the key's right-click
menu, opens them in the permissions editor. **Read** covers reading the
key's values and listing the keys under it, and **Write** covers changing
values and creating keys. The editor adds inheritable grants for
children. Inheritance is computed at creation; changing the parent does
not by itself rewrite keys that already exist. Inspect the actual
descriptors on existing descendants.

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

## Files

**Files**, in the key's pane, takes the key to a file and back. Each
opens a file dialog, where you choose where to save or what to open:

- **Export…** writes the key and everything under it to a *registry
  document*, a JSON file of keys and values that you can read and change
  by hand, and that `reg apply` reads too. It keeps every value exactly.
- **Import…** reads a registry document and, after showing where it
  will write, writes it into the registry, into the layer chosen in the
  bar. It is all or nothing: if any part can't be written, none is.
- **Back up…** copies the key and everything under it, permissions and
  layers included, to a backup file.
- **Restore…** replaces the key's contents and subtree and restores its
  security descriptor from a backup, after asking. It does not merge with
  the current contents.

Backing up needs the privilege to back up files and keys
(SeBackupPrivilege), and restoring the privilege to restore them
(SeRestorePrivilege). Administrators hold both. Without them, the
buttons are shown disabled, with the reason. A backup containing or
matching positive-precedence layers additionally needs `SeTcbPrivilege`
for restore; having the restore privilege alone is not enough.

An export does not include key permissions or the full set of layer
entries. A backup preserves tagged entries, but its layer manifest does
not recreate missing layer definitions. Before recovery after layer
deletion, check whether the needed metadata was included. See
[Backup and restore](~peios/registry-administration/backup-and-restore).

Review the target before importing or restoring. A restore can rewrite
owners and permissions throughout that subtree. If a write or commit
times out or reports a source failure, refresh and inspect state before
retrying; the error does not prove that it was rolled back.

The file dialog shows one folder at a time, starting in your home folder.
Open a folder to go into it; **Up** and **Home** move about, and you can
type a path. It can also make a folder, rename and delete, as you, and
says which of those you may not do, and which folders you may not list.
Saving over a file that is there asks first.

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
`reg del`, with `-r` for a key and everything under it. Export and
import are `reg export --json` and `reg apply`, back up and restore are
`reg backup` and `reg restore`, and layers are `reg layer`. See
[reg](~peios/registry-tools/reg).

## Verify a saved change

After saving, inspect the displayed value, type and winning layer. Use
**Refresh** or **F5** for a fresh read. If a different layer still wins,
check [Layers](~peios/registry-layers/layers) rather than saving repeatedly.

Then follow the manual's application timing and inspect the consuming
component's status and events. An updated row proves what is stored,
not that a service accepted it. Follow
[Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning)
for rejected settings and recovery choices.
