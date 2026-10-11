---
title: Access control on keys
type: reference
description: Diagnose denied registry operations, inspect key and layer permissions, and plan security changes that are not undone by layer recovery.
related:
  - peios/registry-layers/layers
  - peios/registry-concepts/watches
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
  - peios/file-access/the-handle-model
---

A registry operation can need rights on both the target key and the layer
being changed. Start with the operation's error and the exact key; do not
assume that administrator membership or access to a parent grants every
registry operation.

## Inspect the key's permissions

```sh
reg sd Machine/System/KMES
```

Or open **Permissions…** on the key in Registry Editor. A key's security
descriptor contains its owner, DACL and, optionally, SACL. It protects all
values in that key; values do not have separate access controls.

`reg sd` normally shows owner, group and DACL. Reading or changing a SACL
requires the privileged `ACCESS_SYSTEM_SECURITY` right. If inspection is
denied, ask the key's administrator to review the needed operation rather
than broaden access to the entire registry.

## The registry-specific rights

| Intended operation | Required right on the key |
|---|---|
| Read values | `KEY_QUERY_VALUE` |
| Write or delete values | `KEY_SET_VALUE` |
| Create a child key | `KEY_CREATE_SUB_KEY` on the parent |
| List child keys | `KEY_ENUMERATE_SUB_KEYS` |
| Watch changes | `KEY_NOTIFY` |
| Create a link | `KEY_CREATE_SUB_KEY` and `KEY_CREATE_LINK` on the parent, plus `SeTcbPrivilege` or Administrator membership |
| Delete or hide the key | `DELETE` |
| Read its descriptor and metadata | `READ_CONTROL` |
| Change its DACL or owner | `WRITE_DAC` or `WRITE_OWNER`, respectively |
| Read or change its SACL | `ACCESS_SYSTEM_SECURITY` |

The common bundles are `KEY_READ` (query, enumerate, notify and read the
SD), `KEY_WRITE` (set values and create subkeys) and `KEY_ALL_ACCESS`.
Ordinary reads and writes use [AccessCheck](~peios/access-decisions/overview)
against the key; privileges do not grant blanket ordinary registry access.
[Backup and restore](~peios/registry-administration/backup-and-restore)
have their own privilege-gated path.

## Also check the destination layer

A layer-targeted write needs `KEY_SET_VALUE` on that layer's metadata key
under `Machine\System\Registry\Layers\<LayerName>`, as well as the
operation's right on the target key. The layer's displayed owner SID is
informational; its metadata key's security descriptor controls access.

On a stock system, base-layer authorization falls back to a descriptor
that allows Authenticated Users to write into base, while each target key
still controls what they may change.

> [!WARNING]
> Do not create `Machine\System\Registry\Layers\base` just to repair a
> denied write. Creating it replaces the fallback with that key's actual
> descriptor. Ordinary inheritance from `Machine` grants users read access,
> which can prevent their writes even under their own user keys. Review the
> [base-layer authorization rules](~peios/lcs/layers/layer-authorization#the-base-layer-before-it-exists)
> before changing this key.

Creating a layer above precedence 0, or raising a layer's precedence
above 0, additionally requires `SeTcbPrivilege`. Ordinary writes into an
existing layer use the target-key and layer permissions described above.
Deleting a layer requires `DELETE` on its metadata key. See the
[layer rights reference](~peios/lcs/layers/layer-authorization).

## No traversal check

Opening a key checks that key's descriptor, not every ancestor's. If you
know a path, you can sometimes open it even when you cannot list its parent.
Conversely, restricting a parent does not automatically protect every
existing key below it. Inspect the keys containing the data you need to protect.

## Where a key's SD comes from

Inheritance is computed when a key is created. Changing a parent's
permissions later does not automatically rewrite existing descendants;
reapplying inheritance requires a deliberate administrative operation.

The standard root defaults are:

- `Machine`: SYSTEM and Administrators have full control; Authenticated
  Users can read. These grants are inheritable.
- `Users\<SID>`: that user, SYSTEM and Administrators have full control.

A component can set tighter permissions on its own subtree. Verify the
actual descriptor instead of relying on the default description.

## The handle model

Rights are granted when a key is opened and retained on that handle.
Tightening the descriptor affects future opens; it does not revoke an
already-open handle. If an access change must affect a running service,
arrange for it to reopen the key through its documented reload or restart.

## Watching and reading are separate rights

`KEY_NOTIFY` permits watching; `KEY_QUERY_VALUE` permits reading values.
A subtree watcher can learn that a descendant appeared or disappeared
without being allowed to read that descendant's contents. It still must
open the descendant and pass its access check to read it.

## The sharp edge: security is not layered

> [!WARNING]
> A key's owner and permissions are direct properties of the key object.
> Removing or disabling a layer does not restore an earlier descriptor on
> a surviving key. Plan and verify permission recovery separately.

Before a security change, save an appropriate backup and inspect the
current descriptor. Afterward, check the descriptor and test future opens
under the relevant identity. A value that *contains* a descriptor, such
as an SdDefaults override, is a different case: it is layered data, but
changing it does not retroactively rewrite objects already stamped from it.

## Where to go next

- [Security descriptors and inheritance](~peios/security-descriptors/overview)
- [Default descriptors for newly created objects](~peios/registry-security/default-security-descriptors)
- [Privileged backup and restore](~peios/registry-administration/backup-and-restore)
- [LCS access flow](~peios/lcs/security/the-access-flow) for the kernel details
