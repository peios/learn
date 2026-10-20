---
title: The Registry
type: concept
description: How Peios stores configuration as keys and typed values in hives, how layers decide which value wins, who stores the data, and how access to each key is controlled.
related:
  - peios/registry/finding-a-setting
  - peios/registry/changing-a-setting
  - peios/registry/reg
  - peios/registry/registry-editor
---

The registry is where Peios keeps configuration: service definitions, network
profiles, sign-in policy, desktop preferences, and the settings of almost
every component. It is a tree of keys holding typed values. The kernel decides
who can read or change each key. It also lets an installed role, a policy, and
an administrator each set the same value without overwriting one another.
Understanding that model explains why a value you set might not be the one in
effect.

## Hives, keys, and values

A path through the registry names a key, from the top of the tree down:

```text
Machine\System\Services
```

The first part of every path is a **hive**, a top-level tree. A standard
system has two:

- **`Machine`** holds settings for the whole machine.
- **`Users`** holds one subtree for each account, named by the account's
  security identifier (SID): `Users\<SID>`.

`CurrentUser` is a shortcut, not a third hive. At the start of a path, it
stands for `Users\<SID>` of the account the calling program runs as. Other
components can register further hives.

A **key** contains subkeys and values. A **value** is a named piece of data
with a type. A key can also have one value with an empty name, its default
value. The types you meet most are:

| Type | Holds |
|---|---|
| `REG_SZ` | A UTF-8 string |
| `REG_MULTI_SZ` | An ordered list of strings |
| `REG_DWORD` | A 32-bit unsigned integer |
| `REG_QWORD` | A 64-bit unsigned integer |
| `REG_BINARY` | Raw bytes |

Names are case-insensitive but keep the case they were created with, so
`Machine\System\Services` and `machine\system\services` are the same key. The
backslash is the separator. Tools also accept a forward slash, which is easier
to type in a shell.

## Layers

Each value can have several entries at once, one from each **layer** that has
set it. A layer is a named collection of registry writes that can be managed,
and removed, as a unit. When a program reads a value, the kernel returns the
single winning entry: the effective value.

Two numbers decide the winner:

- **Precedence.** Every layer has a precedence. The highest precedence wins.
- **Sequence.** Among layers with the same precedence, the most recent write
  wins.

The **base layer** is built in and is always present. It has precedence 0,
and a write that names no layer goes to it. Layers that a role installs also
sit at precedence 0, so the most recent write among them wins. Policy layers
sit above 0 and override both. Giving a layer a precedence above 0 requires
`SeTcbPrivilege`; being a local administrator doesn't grant it on its own.

Layers make configuration reversible. Deleting a layer removes its entries,
and the next entry down becomes effective again. A layer can also mask a
value, so that the value reads as absent while the layer is in effect.

When a read seems wrong, check which layer won. `reg` and Registry Editor
both report the winning layer for each value.

## Who stores the registry

The kernel holds none of the registry's data. Programs called **sources**
store it, and the kernel asks them for entries when it needs them. On a
standard system, the source is **loregd**, which keeps the `Machine` and
`Users` hives in database files under `/var/state/loregd`.

The kernel makes every decision: which layer wins, who can see a key, and who
can change it. A source only stores what it is given. Programs reading and
writing configuration always talk to the kernel, never to the source.

A key can be **volatile**, which tells its source not to keep it in permanent
storage. loregd holds volatile keys in memory-backed files, so they disappear
whenever loregd restarts, even if the machine doesn't.

If a source stops, its hives become unavailable and requests for them fail
until it returns. Sign-in and other services depend on the registry, so a
storage failure can affect much of the system.
[Diagnosing Registry Storage Failures](~peios/registry/diagnosing-failures)
covers recovery.

## Who can read and change a key

Every key has a security descriptor, which records who owns it and who can
do what to it. The kernel checks the descriptor once, when a program opens
the key, and the program keeps the access it was granted for as long as the
key stays open. Values don't have security descriptors of their own: the
key's descriptor covers all of them.

The kernel checks only the key being opened, not the keys above it. A program
can open `Machine\System\Services\netd` without any access to
`Machine\System\Services`.

Changing a key's security descriptor doesn't affect programs that already
have it open. Security descriptors aren't layered either, so removing a layer
doesn't undo a change to one.

## Documentation and live state

Each component installs a manual for the registry settings it owns. `regman`
reads those manuals. It tells you what a value means, which values are valid,
and when a change takes effect, but it doesn't read the live registry. Use
`reg` or Registry Editor to see what is actually set.

Storing a value doesn't prove that its component accepted it. The component
that reads a setting checks it and decides when to apply it, so check that
component after a change.

## Where to start

These pages cover the tasks:

- [Finding a Registry Setting](~peios/registry/finding-a-setting) to find the
  owner and live state of a setting before you change it.
- [Changing a Registry Setting](~peios/registry/changing-a-setting) to make a
  change from the command line and confirm that it applied.
- [Registry Editor](~peios/registry/registry-editor) to browse and edit the
  registry on the desktop.
- The SDK's [Registry Overview](~peios/sdk-registry/overview) to use the
  registry from your own code.
