---
title: Named roots
type: reference
description: peipkg can operate on several roots at once — named references, dotted composition, default_root, the cascading upgrade, and cross-root dependencies.
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/transactions-and-recovery
  - peios/package-management/dependency-resolution
  - peios/package-management/composing-a-root
---

Before changing an offline installation or an initramfs tree, check which
**root** peipkg will use. With no `--root`, the default is the running system
at `/`; install can also follow a package's `default_root`.

## Check the target before changing it

```
peipkg root list --tree
peipkg root show initramfs
peipkg --root initramfs list
```

Use a registered name such as `initramfs`, or a literal path containing `/`,
such as `/mnt/image` or `./tree`. Put the global option before the command:

```
peipkg --root /mnt/image list
peipkg --root /mnt/image upgrade --dry-run --no-recurse
```

Read the resolved path and status before applying changes. A `dangling` root
has a binding but no target tree; repeating an install does not make that a
valid target. An unregistered name or a resolution cycle is an error.

An upgrade normally resolves the selected root and its reachable named
roots together. Review every target in its combined plan. Use `--no-recurse`
when you intend to update only the selected root. After a cross-root failure,
preserve all participating roots and recover from the same system anchor;
check history and files in each participant afterwards.

## What a named root is

A **named root** is a registered name for a subtree, recorded in the registry of the root it lives under. The name `initramfs` bound to the path `boot/initramfs` is a named root of `/`: it says "within this root, the name `initramfs` means the subtree at `boot/initramfs`, and that subtree is itself a root."

Two ideas follow from that.

**Every root has its own registry.** The bindings a root knows about are its own. `/` may register `initramfs`; what `initramfs` registers is recorded inside `initramfs`, not in `/`. Paths in a registry are stored **relative to the root that owns them**, so a registry travels with its tree — an image built in one place and mounted in another resolves the same way.

**References are resolved from the current root.** The current root is whatever `--root` points at (or `/` when it is omitted). A reference is resolved by starting there and walking its registry.

### Referencing by name

Once `initramfs` is registered under `/`, these two commands target the same tree:

```
$ peipkg --root boot/initramfs install live-boot
$ peipkg --root initramfs install live-boot
```

The second names the root instead of spelling out its path. The name is looked up in the current root's registry and resolved to the bound path.

### Dotted composition

Names compose by dotting. `initramfs.subroot` resolves left to right: from the current root, walk into `initramfs`'s registry, then from there into `subroot`. Each dot is one more step outward through one more registry.

```
$ peipkg --root initramfs.subroot install ...
```

Every dotted segment must match the grammar `[a-z0-9][a-z0-9_-]*` — a lowercase-alphanumeric lead followed by lowercase alphanumerics, hyphens, and underscores. A segment that names no registered root is a **hard error**, not a silent miss. A registry arrangement that loops back on itself is detected and reported as a **resolution cycle** rather than followed forever.

### Path or name: how `--root` decides

`--root` accepts either form and tells them apart by a single rule:

- **Any value containing `/` is a filesystem path** and is used exactly as before — `--root boot/initramfs`, `--root /mnt/image`, `--root ./tree`. This is unchanged behaviour.
- **A bare dotted identifier is a named reference** — `--root initramfs`, `--root initramfs.subroot` — resolved through the registries as above.

The `/` is the discriminator. If you mean a literal directory, include a slash (even `./name`); if you mean a registered name, use the bare identifier.

## The `root` command

`root` manages named roots. **Every subcommand operates on the current root's registry** — the registry of whatever `--root` points at. To manage the initramfs's own named roots, aim `--root` at the initramfs first.

```
peipkg root add <name> <path>
peipkg root remove <name> [--purge]
peipkg root list [--json] [--tree]
peipkg root show <reference> [--json]
```

`root` with no subcommand is a usage error — *a subcommand is required (add, remove, list, show)*. An unknown subcommand is a usage error too.

### `root add`

```
peipkg root add <name> <path>
```

Register a named root in the current root's registry. `<name>` is a single root segment — it must match `[a-z0-9][a-z0-9_-]*` and must not contain a dot; you register one name at a time, not a dotted chain. `<path>` is stored relative to the current root. There are no flags.

```
$ peipkg root add initramfs boot/initramfs
```

### `root remove`

```
peipkg root remove <name> [--purge]
```

Unregister a named root. By default this removes only the **registry entry** — the files on disk are left in place, so the subtree survives and can be re-registered. `--purge` additionally deletes the named root's filesystem tree.

| Option | Effect |
|---|---|
| `--purge` | Also delete the named root's filesystem tree, not just its registry entry. |

### `root list`

```
peipkg root list [--json] [--tree]
```

Print the current root's registry. Plain output lists the names registered directly under the current root.

| Option | Effect |
|---|---|
| `--json` | Emit JSON — for each entry its `name`, its stored `path`, its `resolved_path`, its `status`, and its `children`. |
| `--tree` | Recurse into each child's registry and print the whole nested arrangement. The recursion is cycle-guarded, so a registry that loops is reported rather than followed endlessly. |

### `root show`

```
peipkg root show <reference> [--json]
```

Resolve one reference and report on it. `<reference>` is either a dotted named-root reference or a path — the same path-or-name rule as `--root`. `show` reports the reference's resolved **path**, its **status**, and the number of packages installed in it.

The status is one of two words:

- **`present`** — the resolved path exists on disk and is a real root.
- **`dangling`** — the reference resolves through the registries, but the path it names is not there. The binding exists; the tree it points at does not.

| Option | Effect |
|---|---|
| `--json` | Emit the same report as JSON. |

`present` and `dangling` are the vocabulary the rest of this page uses for "the binding points at something real" versus "the binding is valid but its target is missing".

## Automatic target selection with `default_root`

A package's manifest can declare the root a top-level install of it should land in — its **`default_root`**. When you install such a package without saying where, peipkg reads that field and re-roots the install onto it for you.

```
$ peipkg install live-boot
```

If `live-boot`'s manifest sets `default_root: initramfs`, this installs into the `initramfs` root even though no `--root` was given. The package's manifest records where it belongs, so you do not have to specify it.

Two rules keep this predictable:

- **It applies only when no explicit `--root` was given.** Passing `--root` with any value, including a named one, states the target outright and suppresses `default_root` re-rooting entirely. An explicit root always wins.
- **The packages in one command must agree.** If the packages named in a single install declare two or more distinct default roots, peipkg cannot pick one and does not guess — the command is rejected as an error. Split it into one command per target.

`default_root` only chooses a target; it does not create or resolve anything the registry could not already reach. The chosen root is resolved through the registries like any other named reference.

## Cascading upgrade

By default `peipkg upgrade` resolves one combined plan over the current
root and its reachable named roots. With no package names, it considers the
installed packages in that combined world; a named upgrade considers that
name in every reachable root where it is installed. On a dynamic-initramfs
system, this lets `/` and `boot/initramfs` participate in the same plan.
Review the whole plan before approving it.

If the plan changes more than one root, peipkg uses a coordinated cross-root
transaction. A plan changing only one root uses the single-root executor.
The multi-root sequence is:

1. Lock the participating roots and check pending recovery, then fetch and
   verify the packages for **all** participants before extracting any.
2. Prepare each root. If preparation fails, stop and attempt to roll back
   prepared changes. Rollback can itself fail; the affected journal remains
   pending and the installation must not be treated as restored.
3. Commit package state root by root. A commit failure does not begin an
   independent upgrade in the next root: peipkg continues the coordinated
   commit attempts and reports a partial-commit error. Roots already committed
   remain committed; use [cross-root recovery](#cross-root-undo-and-recovery)
   for the remaining work.

This is not an instantaneous all-files/all-roots switch or a whole-system
snapshot. Files can become visible during preparation, and one root's
post-commit maintenance can run before another root's commit is attempted.
An error is not proof that every participant stayed unchanged.

This sequence follows
[peipkg `8b588ae8`'s upgrade scope](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L188-L223),
[reachable-root planning](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L467-L678),
and [coordinated executor](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L230-L348).
The [prepare/commit boundary](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L554-L655)
and [rollback-failure handling](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L668-L724)
set its limits. These are source-backed behaviours, not a runtime test or
proof that a particular released image contains that revision.

| Option | Effect |
|---|---|
| `--no-recurse` | Confine the upgrade to the current root only. The cascade into nested roots is disabled. |

Use `--no-recurse` when you deliberately want to move just one root — for example to upgrade the initramfs on its own without touching `/`, by pointing `--root` at it and disabling the cascade.

## Cross-root dependencies

Installing a package can pull dependencies into another registered root.
The default upgrade also resolves across reachable roots, as described
above. Review every target before approving: the operation can affect more
than the root you selected.

The [cross-root dependency reference](~peios/peipkg/installation-roots/cross-root-dependencies)
keeps the manifest syntax and routing details, including the separately
documented limits for other verbs and cross-root autoremoval. Removing the
last dependent does not automatically remove its dependency from another
root. Inspect the relevant roots rather than assuming every later operation
repeats the install's routing or cleans up another tree.

A plan that reaches beyond the current root announces it before you approve:

- a `note: this also changes other roots: ...` line naming the other roots the plan touches, and
- a per-line `-> <root>` tag on each plan entry that lands outside the current root, so you can see at a glance which change goes where.

You are never taken across a root boundary silently; a cross-root plan always shows its routing.

## Cross-root undo and recovery

The operator interface describes `undo` of a cross-root transaction as
reversing all participating roots together; there is no supported partial-root
undo of that transaction. Check the history and preview the inverse plan
before applying it.

For an interrupted operation, retain the named-root topology, make every
participant present and reachable, and run `peipkg recover` from the same
anchor, using the original `--root TARGET` if one was selected. The command
discovers reachable roots; it does not establish that missing or unregistered
participants have been found. An ordinary single-root operation refuses
pending cross-root work in isolation.

Recovery rolls pending participants back if none committed. If a participant
has committed, it rolls pending participants forward using their persisted
completion data. Missing or malformed data causes refusal; further recovery
can also fail after another participant has been reconciled. Do not rely on
an interruption leaving all roots at the same version.

In the reviewed source, the CLI can print **rolled back cross-root
transaction** for either recovery direction. That wording is not proof of
rollback. Inspect per-root history and verify files, and treat refused or
unreachable roots as unresolved. Roll-forward recovery also does not invoke
the normal post-commit side-effect runner: do not assume `depmod` or `man-db`
was retried. Follow [Transactions and recovery](~peios/package-management/transactions-and-recovery#across-more-than-one-root)
for the pinned recovery sources, outcome checks and maintenance limits.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | Failure — an unregistered name, a dangling or otherwise invalid reference, a resolution cycle, a failed preparation or rollback, or a cross-root commit or recovery failure. |
| `2` | Usage error — a missing or unknown `root` subcommand, a malformed option, or the wrong number of positional arguments. |
