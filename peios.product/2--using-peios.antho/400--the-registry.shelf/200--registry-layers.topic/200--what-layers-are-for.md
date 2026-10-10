---
title: What layers are for
type: how-to
description: Disable or remove a registry layer deliberately, verify the values that resurface, and keep permissions recovery separate.
related:
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-layers/deleting-keys-and-values
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-concepts/watches
  - peios/registry-concepts/overview
---

Use layers to keep a set of configuration entries removable as a group.
Before disabling or deleting one, identify what manages it and take a
backup of the affected configuration. Removing a layer changes every
entry tagged with that name, not just the key you were inspecting.

<a id="the-payoff-in-one-sentence"></a>
<span id="what-layers-are-for--the-payoff-in-one-sentence"></span>
<span id="registry-layers-what-layers-are-for--the-payoff-in-one-sentence"></span>
<span id="using-peios-registry-layers-what-layers-are-for--the-payoff-in-one-sentence"></span>
<a id="automatic-revert"></a>
<span id="what-layers-are-for--automatic-revert"></span>
<span id="registry-layers-what-layers-are-for--automatic-revert"></span>
<span id="using-peios-registry-layers-what-layers-are-for--automatic-revert"></span>
## Recover from a layer change

1. Run `reg layer ls -l` and inspect important values with `reg get KEY NAME -L`.
2. Confirm the layer is the intended one. For a managed role or policy,
   use its management workflow so registry state and its owner remain in sync.
3. If appropriate, disable the layer to stop its entries participating in
   ordinary resolution while retaining them:

   ```sh
   reg layer set NAME --disable
   ```

4. Re-read the affected keys. The next winning entries may become visible,
   or values and keys may become absent. Verify the consuming services again.
5. Re-enable with `reg layer set NAME --enable` if that is the intended
   recovery. Delete with `reg layer del NAME` only when its entries should
   be removed permanently.

Replace `NAME` with the layer you reviewed. Disabling is not a security
boundary: a disabled layer can still participate for threads whose
credentials name it as a [private layer](~peios/registry-advanced/private-hives-and-layers).

`reg layer del` asks for confirmation on a terminal. With non-terminal
input it proceeds without that prompt. Do not rely on a prompt to protect
an unattended script.

## The base layer

`base` always exists, is enabled at precedence 0 and cannot be disabled
or deleted. Writes go there unless you choose another layer. Repeating a
write in base replaces base's previous entry, so deleting another layer
cannot recover an older base edit.

<a id="saying-no-value-not-just-another-value"></a>
<span id="what-layers-are-for--saying-no-value-not-just-another-value"></span>
<span id="registry-layers-what-layers-are-for--saying-no-value-not-just-another-value"></span>
<span id="using-peios-registry-layers-what-layers-are-for--saying-no-value-not-just-another-value"></span>
## Absence can also come from a layer

A tombstone competes as "no value here". A blanket tombstone does this
for all values on a key; a hidden-key entry masks a key name. Removing
their layer lifts those markers, so configuration previously hidden can
reappear. See [delete, mask and hide](~peios/registry-layers/deleting-keys-and-values).

## Roles

A role can put its registry configuration into a layer. Removing that
layer withdraws its entries and leaves the remaining entries to resolve.
This does not restore a historical snapshot of the entire machine: other
writers may have changed configuration since the role was installed.
A [transaction](~peios/registry-advanced/transactions) is the separate
mechanism for applying related registry changes together.

## Group Policy

Higher-precedence policy continues to win over local edits, regardless
of write order. Lifting a policy layer lets remaining configuration
resurface. Confirm the intended policy through its management workflow;
do not try to defeat it with repeated base-layer writes.

<a id="what-layers-are-not"></a>
<span id="what-layers-are-for--what-layers-are-not"></span>
<span id="registry-layers-what-layers-are-for--what-layers-are-not"></span>
<span id="using-peios-registry-layers-what-layers-are-for--what-layers-are-not"></span>
## What layer removal cannot recover

> [!WARNING]
> A key's security descriptor is not layered. Removing a layer does not
> undo changes to the owner, DACL or SACL of a surviving key. Save and
> review permissions separately when they are part of a change.

Layer removal also does not undo actions already taken by a service, nor
make a consumer accept the values that resurface. It is not a transaction,
a version-history browser or a substitute for a backup.

A backup of an application's subtree preserves its tagged entries but
may not include the layer definitions under `Machine\System\Registry\Layers`.
After layer deletion, such a backup alone may leave the restored entries
inactive. Read [backup scope and layers](~peios/registry-administration/backup-and-restore#backup-is-a-point-in-time-snapshot)
before relying on that recovery path.

## Where to go next

- [Remove one value or key entry](~peios/registry-layers/deleting-keys-and-values)
- [Restore a subtree from a backup](~peios/registry-administration/backup-and-restore)
- [Understand security changes that outlive layers](~peios/registry-security/access-control)
