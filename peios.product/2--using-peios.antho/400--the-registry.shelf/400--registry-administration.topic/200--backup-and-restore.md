---
title: Backup and restore
type: how-to
description: Choose JSON export or a privileged registry backup, plan layer-definition recovery, and restore a subtree without confusing replacement with merge.
related:
  - peios/registry-administration/bootstrap-and-self-configuration
  - peios/registry-administration/lcs-and-sources
  - peios/registry-security/access-control
  - peios/registry-layers/layers
  - peios/registry-concepts/overview
---

Use a **backup** when recovery must preserve a subtree's security
descriptors and tagged layer entries. Use a **JSON export** for a
reviewable configuration document. They serve different purposes.

<a id="backup-and-restore-in-one-sentence"></a>
<span id="backup-and-restore--backup-and-restore-in-one-sentence"></span>
<span id="registry-administration-backup-and-restore--backup-and-restore-in-one-sentence"></span>
<span id="using-peios-registry-administration-backup-and-restore--backup-and-restore-in-one-sentence"></span>
<a id="what-it-is-for"></a>
<span id="backup-and-restore--what-it-is-for"></span>
<span id="registry-administration-backup-and-restore--what-it-is-for"></span>
<span id="using-peios-registry-administration-backup-and-restore--what-it-is-for"></span>
## Choose the recovery format

| Need | Tool | Important limit |
|---|---|---|
| Review or transfer visible keys and values | `reg export --json KEY FILE` and `reg apply FILE` | Export does not save key security descriptors or the complete layered store. |
| Recover a subtree with its descriptors and layer entries | `reg backup KEY FILE` and `reg restore KEY FILE` | Privileged; restore replaces the target contents and descendants. |
| Recover a managed configuration bundle | The role or policy workflow, or a reviewed layer operation | Layer removal does not restore key permissions or reverse consumer side effects. |

Registry Editor offers these under **Files** as **Export…**, **Import…**,
**Back up…** and **Restore…**. Its export is a JSON registry document.
Text-format `reg export` is for review; text input to `reg apply` is not
implemented, so use JSON for reapplication.

## Take a backup before a risky change

For example, to capture the KMES configuration subtree:

```sh
reg backup Machine/System/KMES kmes.snap
```

Confirm the command succeeded and retain the file together with its
original key path and the change it precedes. Choose a protected file
location: backup privilege can include configuration you could not read
through ordinary key access. A failed or interrupted output is not a
verified recovery copy.

## Backup is a point-in-time snapshot

A backup captures a consistent subtree while other writes can continue.
It includes key descriptors, layer-tagged entries and absence markers,
rather than just effective values. The stream has integrity checks to
reject truncation or corruption on restore. Integrity does not establish
that an unknown backup is trustworthy.

> [!WARNING]
> A backup's layer manifest records layer information for validation; it
> does not recreate layer definitions. A layer definition is included only
> if its metadata key under `Machine\System\Registry\Layers\<Name>` is
> part of the backed-up subtree.

If you restore entries for a layer that no longer exists, and the backup
does not restore that layer's metadata, those entries remain inactive
until real metadata exists. This matters when recovering after layer
deletion or moving configuration to another machine. Review which layer
definitions are needed before relying on a narrow subtree snapshot.
See the [LCS backup reference](~peios/lcs/backup-and-restore/backup)
and [restored-layer rules](~peios/lcs/backup-and-restore/restore#layers-in-a-restored-stream).

## Restore is replace, not merge

Before restoring:

1. Confirm the backup is trusted and corresponds to the intended target.
2. Save the current target if you need a way back from the restore itself.
3. Review the target subtree, affected consumers and restored permissions.
4. Confirm needed layer metadata exists or is included, and arrange any
   required privileges or consumer restart/reload.
5. Run restore only after approving the replacement scope.

For the earlier example:

```sh
reg restore Machine/System/KMES kmes.snap
```

The target key object remains, but its mutable fields, values and
contents are restored and its descendants are replaced. Its immutable
volatile/link flags must match the backup root. Do not assume a backup
can be restored onto any arbitrary key.

The operation uses one transaction. A rejected stream or a failure
before commit leaves no partial restored subtree. If the commit times
out or reports a source failure, its result can be uncertain: inspect the
live state before retrying or reporting that nothing changed.

`reg restore` prompts on terminal input; with non-terminal input it
proceeds without that prompt. Do not use a script's lack of a prompt as
evidence that the operation is non-destructive.

## Both bypass per-key permissions — by design

Backup requires `SeBackupPrivilege`; restore requires `SeRestorePrivilege`.
They bypass ordinary per-key checks and are audited independently of each
key's audit settings.

> [!WARNING]
> Restore writes the backed-up security descriptors, including the
> target key's descriptor. Its privilege effectively permits rewriting
> owners and permissions throughout the target subtree.

`SeRestorePrivilege` alone is not enough for every snapshot. A manifest
layer with precedence above 0, or a matching existing layer above 0,
requires `SeTcbPrivilege`. Restored layer metadata is also subject to
its positive-precedence check. See the
[restore precedence gate](~peios/lcs/backup-and-restore/restore#the-precedence-gate).

## Verify the recovery

- Inspect the subtree and representative effective values with `reg tree`,
  `reg get -L` and Registry Editor.
- Inspect key descriptors and `reg layer ls -l`; missing or different
  layer definitions can change what is effective.
- Check relevant consumer status and events after the setting's documented
  application point. Restore notifications require watchers to re-read;
  they are not consumer acceptance acknowledgements.
- Check fresh opens when restored permissions matter; existing handles
  retain the rights granted when they were opened.

## Where to go next

- [Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning)
- [Recover using a layer](~peios/registry-layers/what-layers-are-for)
- [LCS backup and restore implementation](~peios/lcs/backup-and-restore/the-stream)
