---
title: The registry
type: how-to
description: Inspect live registry settings, learn their meaning with regman, make a controlled change, and verify the consuming service before choosing recovery.
related:
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-administration/regman
  - peios/registry-administration/reg
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-concepts/watches
  - peios/security-descriptors/overview
  - peios/file-access/overview
---

Use the registry to inspect and change Peios configuration. Start with the
current value, look up its meaning, and check the program that consumes it
after a change. A successful write alone does not show that the new setting
is in use.

<a id="the-registry-in-one-sentence"></a>
<span id="overview--the-registry-in-one-sentence"></span>
<span id="registry-concepts-overview--the-registry-in-one-sentence"></span>
<span id="using-peios-registry-concepts-overview--the-registry-in-one-sentence"></span>
<a id="where-to-start"></a>
<span id="overview--where-to-start"></span>
<span id="registry-concepts-overview--where-to-start"></span>
<span id="using-peios-registry-concepts-overview--where-to-start"></span>
## Start with a read

These commands only read settings and documentation:

```sh
reg ls Machine/System/KMES -l
reg get Machine/System/KMES BufferCapacity -L
regman 'Machine\System\KMES' BufferCapacity
```

- `reg ls` shows the values and their types.
- `reg get -L` shows the effective value, its winning layer and sequence.
  It does not list all the entries hidden by that winner.
- `regman` explains the expected type, default, valid range and when the
  setting applies. It reads installed documentation, not live state.

If you do not know the path, try `regman -k buffer`, or browse with
[Registry Editor](~peios/registry-administration/registry-editor).
The editor shows the same manual beside each key and value.

## Make one controlled change

1. Read the setting's `regman` entry. Check **Type**, **Valid** and
   **Applies**, including any restart or reboot requirement.
2. Record the old value and winning layer. For recovery that must retain
   permissions and layer entries, take a [backup](~peios/registry-administration/backup-and-restore).
3. Choose the destination layer deliberately. A write needs permission on
   both the key and the layer; higher-precedence policy can keep a local
   write from becoming effective.
4. Change the value with its explicit type, then read it back.
5. Check the consuming component's status and events after the documented
   application point. It may reject the stored value and retain an earlier one.

[Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning)
walks through this sequence. For the desktop controls, use
[Registry Editor](~peios/registry-administration/registry-editor); for all
command options, use [`reg`](~peios/registry-administration/reg).

<a id="the-shape"></a>
<span id="overview--the-shape"></span>
<span id="registry-concepts-overview--the-shape"></span>
<span id="using-peios-registry-concepts-overview--the-shape"></span>
## Know what you are addressing

| Part | Operator meaning |
|---|---|
| Hive | A top-level namespace. `Machine` holds system-wide configuration; `Users` holds users' keys. |
| Key | A container with its own permissions, such as `Machine\System\KMES`. |
| Value | A named, typed setting inside that key, such as `BufferCapacity`. |

`CurrentUser` is an alias for the caller's own `Users\<SID>` key. Paths
are case-insensitive; quote backslash paths in a shell or use forward
slashes with `reg`. The value name is a separate argument, not part of the
key path. See [Keys, values, and types](~peios/registry-concepts/keys-values-and-types).

<a id="what-the-registry-is-not"></a>
<span id="overview--what-the-registry-is-not"></span>
<span id="registry-concepts-overview--what-the-registry-is-not"></span>
<span id="using-peios-registry-concepts-overview--what-the-registry-is-not"></span>
## If the result is unexpected

| Symptom | Check next |
|---|---|
| The write fails with access denied | [Key rights and layer rights](~peios/registry-security/access-control); parent access is not enough. |
| The old value still wins | [Layer precedence and write order](~peios/registry-layers/layers). |
| The new value is stored but behavior is unchanged | [Consumer validation and application timing](~peios/registry-concepts/configuration-and-meaning). |
| A deleted value reappears | [Deletion removes one layer's entry](~peios/registry-layers/deleting-keys-and-values). |
| A write times out or the source fails | [Read state back before retrying](~peios/registry-administration/lcs-and-sources#when-a-source-goes-away). |
| A change needs to be undone | [Layer recovery](~peios/registry-layers/what-layers-are-for) or [backup and restore](~peios/registry-administration/backup-and-restore). |

> [!WARNING]
> Removing a layer does not undo changes to a key's owner or permissions.
> Restore can replace those permissions throughout its target subtree.
> Plan security recovery separately from reverting a value.

<a id="one-registry-built-from-two-parts"></a>
<span id="overview--one-registry-built-from-two-parts"></span>
<span id="registry-concepts-overview--one-registry-built-from-two-parts"></span>
<span id="using-peios-registry-concepts-overview--one-registry-built-from-two-parts"></span>
## When you need implementation detail

Applications and tools reach the registry through the kernel's Layered
Configuration Subsystem (LCS). Userspace sources persist its data;
`loregd` supplies the default `registryd` role. You do not edit their
backing databases to change a setting.

The [source operations guide](~peios/registry-administration/lcs-and-sources)
covers availability and trust. The [kernel LCS TRM](~peios/lcs/overview)
covers the data model, syscall ABI, watch implementation and source protocol.
