---
title: Named roots
type: reference
description: "peipkg can install into more than one root at once. This page explains named roots, the per-root registry, dotted references, automatic target selection with default_root, the cascading upgrade, cross-root dependencies and their two-phase commit, and how undo and recover treat a cross-root change as a unit."
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/transactions-and-recovery
  - peios/package-management/dependency-resolution
  - peios/package-management/composing-a-root
---

Every peipkg command runs against a **root** — a subtree it treats as a complete Peios installation. By default that root is `/`, the running system. The [`--root DIR`](~peios/package-management/overview) global option points peipkg at a different one: an image mounted at `DIR`, an offline system under maintenance, a tree being built.

A single bare path is enough when there is exactly one alternate tree and you always spell it out in full. It stops being enough when a system is several cooperating trees that are built and kept current together. Peios's **dynamic initramfs** is the case that motivates this page: a real system root at `/` and an initramfs image at `boot/initramfs`, both assembled from ordinary packages, both upgraded by the same package manager. Passing `--root boot/initramfs` on every command that touches the image — and remembering that path everywhere — is the friction named roots remove.

So `--root` generalises. A root can **register** other roots under it by name, reference them by that name instead of a path, compose those names by dotting, install a dependency into a *different* root than its depender, and upgrade every nested root in one command. The mechanism is deliberately general — the initramfs is one arrangement it expresses, not a special case wired into the tool.

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

By default `peipkg upgrade` reconciles the current root and every named root nested under it, recursively — the whole tree of roots, in one command. Run it against `/` on a dynamic-initramfs system and both `/` and `boot/initramfs` are brought current together.

Each root is upgraded as an independent transaction that continues on error: peipkg walks the tree, upgrades each root on its own, and prints a per-root summary. One root's failure does not abort the others — a broken upgrade in `initramfs` leaves `/`'s upgrade to complete and report normally, and vice versa. You get one summary per root and a clear picture of which succeeded.

Each of those per-root upgrades is an ordinary transaction with the full atomic guarantee of [Transactions and recovery](~peios/package-management/transactions-and-recovery); the cascade runs several of them, it does not weaken any one.

| Option | Effect |
|---|---|
| `--no-recurse` | Confine the upgrade to the current root only. The cascade into nested roots is disabled. |

Use `--no-recurse` when you deliberately want to move just one root — for example to upgrade the initramfs on its own without touching `/`, by pointing `--root` at it and disabling the cascade.

## Cross-root dependencies

A dependency can be routed into a different root than the package that declares it. A manifest writes this with `IN`:

```
Depends: foo IN initramfs
```

This says "I depend on `foo`, and `foo` belongs in the `initramfs` root" — the root name is resolved through the registries from the depending package's root. It is what lets a whole root be composed out of ordinary packages through the dependency graph: a single package installed into `/` can pull the pieces of the initramfs into `initramfs` as its dependencies, so the image is built by the same resolver and the same packages as everything else. An image builder starting from nothing can assemble an entire multi-root arrangement like this offline, from a declarative manifest, with the separate `peipkg-compose` binary — see [Composing a root](~peios/package-management/composing-a-root).

`install` is the only verb that crosses roots. When resolution produces a plan whose changes land in more than one root, that plan is committed as a **two-phase commit** across the participating roots, under a single generated **cross-root transaction id** that ties the per-root pieces together. Either the change lands in every participating root or in none — the multi-root plan is atomic as a whole, not merely per root.

A plan that reaches beyond the current root announces it before you approve:

- a `note: this also changes other roots: ...` line naming the other roots the plan touches, and
- a per-line `-> <root>` tag on each plan entry that lands outside the current root, so you can see at a glance which change goes where.

You are never taken across a root boundary silently; a cross-root plan always shows its routing.

## Cross-root undo and recovery

Because a cross-root install commits as a unit, it reverses as a unit.

**`undo`** on a cross-root transaction reverses all of its participating roots together. There is no way to walk back only the `/` half of a change that also touched `initramfs` — the cross-root transaction id binds the pieces, and `undo` reverses the whole. See [Keeping a system current](~peios/package-management/keeping-a-system-current) for `undo` in general.

**`recover`** understands cross-root transactions too. It reconciles them across every reachable root, walking the registry outward from the current root to find each participant. A cross-root commit that was torn by an interruption is resolved the same way a single-root one is — with one addition that follows from the two-phase commit: a torn commit is rolled back if it was interrupted before its point of no return, or rolled forward to completion if it had already passed that point. Either way every participating root ends in the same, consistent state.

This is the single-root recovery model of [Transactions and recovery](~peios/package-management/transactions-and-recovery) extended across roots: the same commit-instant guarantee, now applied to a commit that spans several trees at once. Read that page for the underlying transaction model this builds on.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | Failure — an unregistered name, a dangling or otherwise invalid reference, a resolution cycle, a per-root transaction that failed, or a cross-root commit failure. |
| `2` | Usage error — a missing or unknown `root` subcommand, a malformed option, or the wrong number of positional arguments. |
